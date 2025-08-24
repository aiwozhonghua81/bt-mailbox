#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI垃圾邮件检测服务
基于机器学习的智能垃圾邮件识别系统
支持中英文邮件内容分析和实时检测
"""

import os
import re
import json
import pickle
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import jieba
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

# Redis缓存
import redis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mailbox/spam_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SpamDetector:
    """垃圾邮件检测器"""
    
    def __init__(self, model_path: str = '/opt/bt-mailbox/models'):
        self.model_path = model_path
        self.models = {}
        self.vectorizers = {}
        self.redis_client = None
        self.stemmer = PorterStemmer()
        
        # 确保模型目录存在
        os.makedirs(model_path, exist_ok=True)
        
        # 初始化Redis连接
        self._init_redis()
        
        # 下载NLTK数据
        self._download_nltk_data()
        
        # 加载或训练模型
        self._load_or_train_models()
        
        # 垃圾邮件关键词库
        self.spam_keywords = {
            'en': [
                'viagra', 'cialis', 'lottery', 'winner', 'congratulations',
                'free money', 'click here', 'urgent', 'limited time',
                'act now', 'guaranteed', 'risk free', 'no obligation',
                'credit card', 'loan', 'debt', 'refinance', 'mortgage'
            ],
            'zh': [
                '中奖', '恭喜', '免费', '赚钱', '贷款', '信用卡',
                '点击', '立即', '限时', '保证', '无风险', '优惠',
                '特价', '促销', '折扣', '返利', '投资', '理财'
            ]
        }
        
        # 白名单域名
        self.whitelist_domains = [
            'windsurf.com', 'github.com', 'google.com', 'microsoft.com',
            'apple.com', 'amazon.com', 'facebook.com', 'twitter.com'
        ]
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host='127.0.0.1',
                port=6379,
                db=2,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def _download_nltk_data(self):
        """下载NLTK必要数据"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
        except Exception as e:
            logger.warning(f"NLTK数据下载失败: {e}")
    
    def _load_or_train_models(self):
        """加载或训练模型"""
        model_files = {
            'nb': 'naive_bayes.pkl',
            'rf': 'random_forest.pkl',
            'lr': 'logistic_regression.pkl'
        }
        
        vectorizer_file = 'tfidf_vectorizer.pkl'
        
        # 检查模型文件是否存在
        all_exist = all(
            os.path.exists(os.path.join(self.model_path, f))
            for f in list(model_files.values()) + [vectorizer_file]
        )
        
        if all_exist:
            self._load_models(model_files, vectorizer_file)
        else:
            logger.info("模型文件不存在，开始训练新模型...")
            self._train_models(model_files, vectorizer_file)
    
    def _load_models(self, model_files: Dict[str, str], vectorizer_file: str):
        """加载预训练模型"""
        try:
            # 加载向量化器
            with open(os.path.join(self.model_path, vectorizer_file), 'rb') as f:
                self.vectorizers['tfidf'] = pickle.load(f)
            
            # 加载分类器
            for name, filename in model_files.items():
                with open(os.path.join(self.model_path, filename), 'rb') as f:
                    self.models[name] = pickle.load(f)
            
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self._train_models(model_files, vectorizer_file)
    
    def _train_models(self, model_files: Dict[str, str], vectorizer_file: str):
        """训练新模型"""
        try:
            # 生成训练数据
            X_train, X_test, y_train, y_test = self._generate_training_data()
            
            # 创建TF-IDF向量化器
            self.vectorizers['tfidf'] = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95
            )
            
            # 向量化训练数据
            X_train_vec = self.vectorizers['tfidf'].fit_transform(X_train)
            X_test_vec = self.vectorizers['tfidf'].transform(X_test)
            
            # 训练多个模型
            classifiers = {
                'nb': MultinomialNB(alpha=0.1),
                'rf': RandomForestClassifier(n_estimators=100, random_state=42),
                'lr': LogisticRegression(random_state=42, max_iter=1000)
            }
            
            for name, clf in classifiers.items():
                logger.info(f"训练{name}模型...")
                clf.fit(X_train_vec, y_train)
                
                # 评估模型
                y_pred = clf.predict(X_test_vec)
                accuracy = accuracy_score(y_test, y_pred)
                logger.info(f"{name}模型准确率: {accuracy:.4f}")
                
                self.models[name] = clf
            
            # 保存模型
            self._save_models(model_files, vectorizer_file)
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            # 使用默认规则
            self._init_default_rules()
    
    def _generate_training_data(self) -> Tuple[List[str], List[str], List[int], List[int]]:
        """生成训练数据"""
        # 垃圾邮件样本
        spam_samples = [
            "Congratulations! You've won $1,000,000! Click here to claim now!",
            "Free Viagra! Buy now and get 50% off! Limited time offer!",
            "Urgent: Your account will be closed. Click here immediately!",
            "Make money fast! Work from home! No experience needed!",
            "中奖通知：恭喜您获得100万大奖！立即点击领取！",
            "免费贷款！无抵押！当天放款！点击申请！",
            "紧急通知：您的账户异常，请立即点击验证！",
            "投资理财！日赚千元！零风险！马上加入！"
        ]
        
        # 正常邮件样本
        ham_samples = [
            "Hi, this is a reminder about our meeting tomorrow at 2 PM.",
            "Thank you for your order. Your package will arrive in 3-5 days.",
            "Your verification code for windsurf.com is: 123456",
            "Meeting minutes from today's conference call are attached.",
            "您好，这是关于明天下午2点会议的提醒。",
            "感谢您的订购，您的包裹将在3-5天内送达。",
            "您的windsurf.com验证码是：123456",
            "今天电话会议的会议纪要已附上。"
        ]
        
        # 扩展训练数据
        spam_extended = []
        ham_extended = []
        
        # 通过组合和变换生成更多样本
        for _ in range(500):
            # 生成垃圾邮件变体
            spam_base = np.random.choice(spam_samples)
            spam_extended.append(self._add_noise(spam_base))
            
            # 生成正常邮件变体
            ham_base = np.random.choice(ham_samples)
            ham_extended.append(self._add_noise(ham_base))
        
        # 合并数据
        all_spam = spam_samples + spam_extended
        all_ham = ham_samples + ham_extended
        
        X = all_spam + all_ham
        y = [1] * len(all_spam) + [0] * len(all_ham)
        
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def _add_noise(self, text: str) -> str:
        """为文本添加噪声以增加样本多样性"""
        # 随机替换一些字符
        chars = list(text)
        if len(chars) > 10:
            num_changes = np.random.randint(1, min(3, len(chars) // 10))
            for _ in range(num_changes):
                idx = np.random.randint(0, len(chars))
                if chars[idx].isalpha():
                    chars[idx] = np.random.choice(['a', 'e', 'i', 'o', 'u'])
        
        return ''.join(chars)
    
    def _save_models(self, model_files: Dict[str, str], vectorizer_file: str):
        """保存训练好的模型"""
        try:
            # 保存向量化器
            with open(os.path.join(self.model_path, vectorizer_file), 'wb') as f:
                pickle.dump(self.vectorizers['tfidf'], f)
            
            # 保存分类器
            for name, filename in model_files.items():
                with open(os.path.join(self.model_path, filename), 'wb') as f:
                    pickle.dump(self.models[name], f)
            
            logger.info("模型保存成功")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
    
    def _init_default_rules(self):
        """初始化默认规则（当ML模型不可用时）"""
        logger.info("使用默认规则进行垃圾邮件检测")
        self.use_ml_models = False
    
    def preprocess_text(self, text: str, language: str = 'auto') -> str:
        """预处理文本"""
        if not text:
            return ""
        
        # 转换为小写
        text = text.lower()
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 移除邮箱地址
        text = re.sub(r'\S+@\S+', '', text)
        
        # 移除特殊字符，保留字母数字和空格
        text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', ' ', text)
        
        # 检测语言
        if language == 'auto':
            language = self._detect_language(text)
        
        # 分词和词干提取
        if language == 'zh':
            # 中文分词
            words = jieba.lcut(text)
            # 移除停用词
            stop_words = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
            words = [w for w in words if w not in stop_words and len(w) > 1]
        else:
            # 英文分词
            words = word_tokenize(text)
            # 移除停用词
            try:
                stop_words = set(stopwords.words('english'))
                words = [self.stemmer.stem(w) for w in words if w not in stop_words and len(w) > 2]
            except:
                words = [w for w in words if len(w) > 2]
        
        return ' '.join(words)
    
    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return 'en'
        
        chinese_ratio = chinese_chars / total_chars
        return 'zh' if chinese_ratio > 0.3 else 'en'
    
    def extract_features(self, email_data: Dict) -> Dict:
        """提取邮件特征"""
        features = {}
        
        # 基础特征
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('from', '')
        
        # 文本特征
        features['subject_length'] = len(subject)
        features['body_length'] = len(body)
        features['has_html'] = 1 if '<html>' in body.lower() or '<body>' in body.lower() else 0
        
        # 发件人特征
        features['sender_domain'] = sender.split('@')[-1] if '@' in sender else ''
        features['is_whitelist_domain'] = 1 if features['sender_domain'] in self.whitelist_domains else 0
        
        # 关键词特征
        combined_text = f"{subject} {body}".lower()
        features['spam_keywords_en'] = sum(1 for kw in self.spam_keywords['en'] if kw in combined_text)
        features['spam_keywords_zh'] = sum(1 for kw in self.spam_keywords['zh'] if kw in combined_text)
        
        # URL和链接特征
        features['url_count'] = len(re.findall(r'http[s]?://\S+', combined_text))
        features['email_count'] = len(re.findall(r'\S+@\S+', combined_text))
        
        # 特殊字符特征
        features['exclamation_count'] = combined_text.count('!')
        features['question_count'] = combined_text.count('?')
        features['dollar_count'] = combined_text.count('$')
        features['percent_count'] = combined_text.count('%')
        
        # 大写字母比例
        if len(combined_text) > 0:
            features['uppercase_ratio'] = sum(1 for c in combined_text if c.isupper()) / len(combined_text)
        else:
            features['uppercase_ratio'] = 0
        
        return features
    
    def predict_spam(self, email_data: Dict) -> Dict:
        """预测邮件是否为垃圾邮件"""
        try:
            # 生成缓存键
            email_hash = hashlib.md5(
                f"{email_data.get('subject', '')}{email_data.get('body', '')}".encode()
            ).hexdigest()
            cache_key = f"spam_prediction:{email_hash}"
            
            # 检查缓存
            if self.redis_client:
                try:
                    cached_result = self.redis_client.get(cache_key)
                    if cached_result:
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(f"Redis缓存读取失败: {e}")
            
            # 预处理文本
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            combined_text = f"{subject} {body}"
            processed_text = self.preprocess_text(combined_text)
            
            # 提取特征
            features = self.extract_features(email_data)
            
            # 使用ML模型预测
            if hasattr(self, 'use_ml_models') and not self.use_ml_models:
                # 使用规则预测
                result = self._rule_based_prediction(features, processed_text)
            else:
                # 使用ML模型预测
                result = self._ml_prediction(processed_text, features)
            
            # 缓存结果
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, 3600, json.dumps(result))  # 缓存1小时
                except Exception as e:
                    logger.warning(f"Redis缓存写入失败: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"垃圾邮件预测失败: {e}")
            return {
                'is_spam': False,
                'confidence': 0.0,
                'method': 'error',
                'features': {},
                'error': str(e)
            }
    
    def _ml_prediction(self, processed_text: str, features: Dict) -> Dict:
        """使用机器学习模型预测"""
        try:
            # 向量化文本
            text_features = self.vectorizers['tfidf'].transform([processed_text])
            
            # 获取多个模型的预测
            predictions = {}
            probabilities = {}
            
            for name, model in self.models.items():
                pred = model.predict(text_features)[0]
                prob = model.predict_proba(text_features)[0]
                predictions[name] = pred
                probabilities[name] = prob[1]  # 垃圾邮件概率
            
            # 集成预测（投票）
            spam_votes = sum(predictions.values())
            total_votes = len(predictions)
            avg_probability = np.mean(list(probabilities.values()))
            
            is_spam = spam_votes > total_votes / 2
            confidence = avg_probability
            
            return {
                'is_spam': bool(is_spam),
                'confidence': float(confidence),
                'method': 'ml_ensemble',
                'model_predictions': predictions,
                'model_probabilities': probabilities,
                'features': features,
                'processed_text_length': len(processed_text)
            }
            
        except Exception as e:
            logger.error(f"ML预测失败: {e}")
            return self._rule_based_prediction(features, processed_text)
    
    def _rule_based_prediction(self, features: Dict, processed_text: str) -> Dict:
        """基于规则的预测"""
        spam_score = 0
        reasons = []
        
        # 白名单域名检查
        if features.get('is_whitelist_domain', 0):
            return {
                'is_spam': False,
                'confidence': 0.1,
                'method': 'whitelist',
                'features': features,
                'reasons': ['发件人域名在白名单中']
            }
        
        # 关键词检查
        spam_keywords_total = features.get('spam_keywords_en', 0) + features.get('spam_keywords_zh', 0)
        if spam_keywords_total > 0:
            spam_score += spam_keywords_total * 0.3
            reasons.append(f'包含{spam_keywords_total}个垃圾邮件关键词')
        
        # URL数量检查
        if features.get('url_count', 0) > 3:
            spam_score += 0.4
            reasons.append('包含过多URL链接')
        
        # 特殊字符检查
        if features.get('exclamation_count', 0) > 3:
            spam_score += 0.2
            reasons.append('包含过多感叹号')
        
        # 大写字母比例检查
        if features.get('uppercase_ratio', 0) > 0.5:
            spam_score += 0.3
            reasons.append('大写字母比例过高')
        
        # 邮件长度检查
        if features.get('body_length', 0) < 50 and features.get('url_count', 0) > 0:
            spam_score += 0.2
            reasons.append('邮件内容过短但包含链接')
        
        is_spam = spam_score > 0.5
        confidence = min(spam_score, 1.0)
        
        return {
            'is_spam': is_spam,
            'confidence': confidence,
            'method': 'rule_based',
            'features': features,
            'spam_score': spam_score,
            'reasons': reasons
        }
    
    def update_model(self, feedback_data: List[Dict]):
        """根据用户反馈更新模型"""
        try:
            if not feedback_data:
                return
            
            logger.info(f"收到{len(feedback_data)}条反馈数据，开始更新模型...")
            
            # 准备训练数据
            texts = []
            labels = []
            
            for item in feedback_data:
                text = f"{item.get('subject', '')} {item.get('body', '')}"
                processed_text = self.preprocess_text(text)
                texts.append(processed_text)
                labels.append(1 if item.get('is_spam') else 0)
            
            if len(texts) < 10:
                logger.warning("反馈数据太少，跳过模型更新")
                return
            
            # 向量化
            X_new = self.vectorizers['tfidf'].transform(texts)
            
            # 增量学习（对于支持的模型）
            for name, model in self.models.items():
                if hasattr(model, 'partial_fit'):
                    model.partial_fit(X_new, labels)
                    logger.info(f"模型{name}增量更新完成")
            
            # 保存更新后的模型
            model_files = {
                'nb': 'naive_bayes.pkl',
                'rf': 'random_forest.pkl',
                'lr': 'logistic_regression.pkl'
            }
            self._save_models(model_files, 'tfidf_vectorizer.pkl')
            
        except Exception as e:
            logger.error(f"模型更新失败: {e}")
    
    def get_statistics(self) -> Dict:
        """获取检测统计信息"""
        try:
            stats = {
                'total_predictions': 0,
                'spam_detected': 0,
                'ham_detected': 0,
                'accuracy_rate': 0.0,
                'model_info': {},
                'cache_hits': 0,
                'last_updated': datetime.now().isoformat()
            }
            
            if self.redis_client:
                try:
                    # 从Redis获取统计信息
                    stats['total_predictions'] = int(self.redis_client.get('spam_stats:total') or 0)
                    stats['spam_detected'] = int(self.redis_client.get('spam_stats:spam') or 0)
                    stats['ham_detected'] = int(self.redis_client.get('spam_stats:ham') or 0)
                    stats['cache_hits'] = int(self.redis_client.get('spam_stats:cache_hits') or 0)
                except Exception as e:
                    logger.warning(f"获取Redis统计信息失败: {e}")
            
            # 模型信息
            for name, model in self.models.items():
                stats['model_info'][name] = {
                    'type': type(model).__name__,
                    'features': getattr(model, 'n_features_in_', 'unknown')
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

def main():
    """主函数 - 用于测试"""
    detector = SpamDetector()
    
    # 测试邮件
    test_emails = [
        {
            'subject': 'Congratulations! You won $1,000,000!',
            'body': 'Click here now to claim your prize! Limited time offer!',
            'from': 'noreply@spam.com'
        },
        {
            'subject': 'Your windsurf.com verification code',
            'body': 'Your verification code is: 123456. Please enter this code to complete your registration.',
            'from': 'noreply@windsurf.com'
        }
    ]
    
    for i, email in enumerate(test_emails):
        result = detector.predict_spam(email)
        print(f"\n邮件 {i+1}:")
        print(f"主题: {email['subject']}")
        print(f"是否垃圾邮件: {result['is_spam']}")
        print(f"置信度: {result['confidence']:.4f}")
        print(f"检测方法: {result['method']}")

if __name__ == '__main__':
    main()
