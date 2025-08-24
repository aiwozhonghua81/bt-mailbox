<template>
  <div id="app">
    <!-- 登录页面 -->
    <div v-if="!isAuthenticated" class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h2><i class="el-icon-message"></i> 企业级邮箱系统</h2>
          <p>管理员登录</p>
        </div>
        <el-form 
          ref="loginForm" 
          :model="loginForm" 
          :rules="loginRules" 
          class="login-form"
          @submit.native.prevent="handleLogin"
        >
          <el-form-item prop="email">
            <el-input
              v-model="loginForm.email"
              placeholder="邮箱地址"
              prefix-icon="el-icon-user"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              prefix-icon="el-icon-lock"
              size="large"
              show-password
              @keyup.enter.native="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="loginLoading"
              style="width: 100%"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 主应用界面 -->
    <div v-else class="app-container">
      <!-- 顶部导航 -->
      <el-header class="app-header">
        <div class="header-left">
          <h3><i class="el-icon-message"></i> 企业级邮箱系统</h3>
        </div>
        <div class="header-right">
          <el-badge :value="unreadCount" class="notification-badge">
            <el-button icon="el-icon-bell" circle @click="showNotifications"></el-button>
          </el-badge>
          <el-dropdown @command="handleUserCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" icon="el-icon-user-solid"></el-avatar>
              <span class="username">{{ currentUser.name || currentUser.email }}</span>
              <i class="el-icon-arrow-down"></i>
            </span>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="profile">个人资料</el-dropdown-item>
              <el-dropdown-item command="settings">系统设置</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="250px" class="app-sidebar">
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="dashboard">
              <i class="el-icon-data-analysis"></i>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="users">
              <i class="el-icon-user"></i>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="domains">
              <i class="el-icon-globe"></i>
              <span>域名管理</span>
            </el-menu-item>
            <el-menu-item index="mail-logs">
              <i class="el-icon-document"></i>
              <span>邮件日志</span>
            </el-menu-item>
            <el-menu-item index="ai-features">
              <i class="el-icon-cpu"></i>
              <span>AI功能</span>
            </el-menu-item>
            <el-menu-item index="monitoring">
              <i class="el-icon-monitor"></i>
              <span>系统监控</span>
            </el-menu-item>
            <el-menu-item index="settings">
              <i class="el-icon-setting"></i>
              <span>系统设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主内容区 -->
        <el-main class="app-main">
          <!-- 仪表盘 -->
          <div v-if="activeMenu === 'dashboard'" class="dashboard">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon users">
                  <i class="el-icon-user"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ stats.users?.total || 0 }}</div>
                  <div class="stat-label">用户总数</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon active">
                  <i class="el-icon-check"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ stats.users?.active || 0 }}</div>
                  <div class="stat-label">活跃用户</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon mails">
                  <i class="el-icon-message"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ stats.mails?.today || 0 }}</div>
                  <div class="stat-label">今日邮件</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon system">
                  <i class="el-icon-cpu"></i>
                </div>
                <div class="stat-content">
                  <div class="stat-number">{{ (stats.system?.cpu_percent || 0).toFixed(1) }}%</div>
                  <div class="stat-label">CPU使用率</div>
                </div>
              </div>
            </div>

            <!-- 系统监控图表 -->
            <div class="charts-container">
              <el-card class="chart-card">
                <div slot="header">
                  <span>系统资源使用情况</span>
                  <el-button style="float: right; padding: 3px 0" type="text" @click="refreshStats">刷新</el-button>
                </div>
                <div id="systemChart" style="height: 300px;"></div>
              </el-card>
              
              <el-card class="chart-card">
                <div slot="header">
                  <span>服务状态</span>
                </div>
                <div class="services-status">
                  <div 
                    v-for="service in stats.services" 
                    :key="service.name"
                    class="service-item"
                  >
                    <span class="service-name">{{ service.display_name }}</span>
                    <el-tag 
                      :type="service.status === 'running' ? 'success' : 'danger'"
                      size="small"
                    >
                      {{ service.status === 'running' ? '运行中' : '已停止' }}
                    </el-tag>
                  </div>
                </div>
              </el-card>
            </div>
          </div>

          <!-- 用户管理 -->
          <div v-if="activeMenu === 'users'" class="users-management">
            <div class="page-header">
              <h3>用户管理</h3>
              <el-button type="primary" @click="showAddUserDialog">
                <i class="el-icon-plus"></i> 添加用户
              </el-button>
            </div>

            <el-card>
              <div class="table-toolbar">
                <el-input
                  v-model="userSearch"
                  placeholder="搜索用户..."
                  style="width: 300px;"
                  @input="searchUsers"
                >
                  <i slot="prefix" class="el-icon-search"></i>
                </el-input>
              </div>

              <el-table 
                :data="users" 
                v-loading="usersLoading"
                style="width: 100%"
              >
                <el-table-column prop="id" label="ID" width="80"></el-table-column>
                <el-table-column prop="email" label="邮箱地址"></el-table-column>
                <el-table-column prop="name" label="姓名"></el-table-column>
                <el-table-column prop="quota" label="配额(MB)" width="120"></el-table-column>
                <el-table-column label="状态" width="100">
                  <template slot-scope="scope">
                    <el-tag :type="scope.row.enabled ? 'success' : 'danger'" size="small">
                      {{ scope.row.enabled ? '启用' : '禁用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180">
                  <template slot-scope="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template slot-scope="scope">
                    <el-button size="mini" @click="editUser(scope.row)">编辑</el-button>
                    <el-button 
                      size="mini" 
                      :type="scope.row.enabled ? 'warning' : 'success'"
                      @click="toggleUserStatus(scope.row)"
                    >
                      {{ scope.row.enabled ? '禁用' : '启用' }}
                    </el-button>
                    <el-button size="mini" type="danger" @click="deleteUser(scope.row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
                :current-page="currentPage"
                :page-sizes="[10, 20, 50, 100]"
                :page-size="pageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="totalUsers"
                style="margin-top: 20px; text-align: right;"
              >
              </el-pagination>
            </el-card>
          </div>

          <!-- AI功能 -->
          <div v-if="activeMenu === 'ai-features'" class="ai-features">
            <div class="page-header">
              <h3>AI智能功能</h3>
            </div>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-card>
                  <div slot="header">
                    <span>垃圾邮件检测</span>
                  </div>
                  <div class="ai-stats">
                    <div class="ai-stat-item">
                      <span class="label">总检测次数:</span>
                      <span class="value">{{ aiStats.total_predictions || 0 }}</span>
                    </div>
                    <div class="ai-stat-item">
                      <span class="label">垃圾邮件检出:</span>
                      <span class="value">{{ aiStats.spam_detected || 0 }}</span>
                    </div>
                    <div class="ai-stat-item">
                      <span class="label">正常邮件:</span>
                      <span class="value">{{ aiStats.ham_detected || 0 }}</span>
                    </div>
                  </div>
                  <el-button type="primary" @click="testSpamDetection">测试检测</el-button>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <div slot="header">
                    <span>邮件分类</span>
                  </div>
                  <div class="ai-feature-item">
                    <p>智能邮件分类功能可以自动将邮件分类到不同文件夹。</p>
                    <el-button type="success">启用分类</el-button>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 邮件日志 -->
          <div v-if="activeMenu === 'mail-logs'" class="mail-logs">
            <div class="page-header">
              <h3>邮件日志</h3>
            </div>

            <el-card>
              <div class="table-toolbar">
                <el-select v-model="logFilter" placeholder="状态筛选" style="width: 120px; margin-right: 10px;">
                  <el-option label="全部" value=""></el-option>
                  <el-option label="已接收" value="received"></el-option>
                  <el-option label="垃圾邮件" value="spam"></el-option>
                  <el-option label="已阻止" value="blocked"></el-option>
                </el-select>
                <el-button @click="loadMailLogs">刷新</el-button>
              </div>

              <el-table :data="mailLogs" v-loading="logsLoading" style="width: 100%">
                <el-table-column prop="id" label="ID" width="80"></el-table-column>
                <el-table-column prop="sender" label="发件人"></el-table-column>
                <el-table-column prop="recipient" label="收件人"></el-table-column>
                <el-table-column prop="subject" label="主题" show-overflow-tooltip></el-table-column>
                <el-table-column label="状态" width="100">
                  <template slot-scope="scope">
                    <el-tag 
                      :type="getStatusType(scope.row.status)" 
                      size="small"
                    >
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="时间" width="180">
                  <template slot-scope="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>

          <!-- 域名管理 -->
          <div v-if="activeMenu === 'domains'" class="domains-management">
            <div class="page-header">
              <h3>域名管理</h3>
              <el-button type="primary" @click="showAddDomainDialog">
                <i class="el-icon-plus"></i> 添加域名
              </el-button>
            </div>

            <el-card>
              <div class="table-toolbar">
                <el-input
                  v-model="domainSearch"
                  placeholder="搜索域名..."
                  style="width: 300px;"
                  @input="searchDomains"
                >
                  <i slot="prefix" class="el-icon-search"></i>
                </el-input>
              </div>

              <el-table 
                :data="domains" 
                v-loading="domainsLoading"
                style="width: 100%"
              >
                <el-table-column prop="id" label="ID" width="80"></el-table-column>
                <el-table-column prop="domain" label="域名"></el-table-column>
                <el-table-column label="状态" width="100">
                  <template slot-scope="scope">
                    <el-tag :type="scope.row.active ? 'success' : 'danger'" size="small">
                      {{ scope.row.active ? '活跃' : '停用' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="user_count" label="用户数量" width="120">
                  <template slot-scope="scope">
                    <el-badge :value="scope.row.user_count" class="item">
                      <span>{{ scope.row.user_count || 0 }}</span>
                    </el-badge>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180">
                  <template slot-scope="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200">
                  <template slot-scope="scope">
                    <el-button size="mini" @click="editDomain(scope.row)">编辑</el-button>
                    <el-button 
                      size="mini" 
                      :type="scope.row.active ? 'warning' : 'success'"
                      @click="toggleDomainStatus(scope.row)"
                    >
                      {{ scope.row.active ? '停用' : '启用' }}
                    </el-button>
                    <el-button size="mini" type="danger" @click="deleteDomain(scope.row)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>

              <el-pagination
                @size-change="handleDomainSizeChange"
                @current-change="handleDomainCurrentChange"
                :current-page="domainCurrentPage"
                :page-sizes="[10, 20, 50, 100]"
                :page-size="domainPageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="totalDomains"
                style="margin-top: 20px; text-align: right;"
              >
              </el-pagination>
            </el-card>
          </div>

          <!-- 系统监控 -->
          <div v-if="activeMenu === 'monitoring'" class="monitoring">
            <div class="page-header">
              <h3>系统监控</h3>
              <el-button @click="refreshMonitoringData">
                <i class="el-icon-refresh"></i> 刷新数据
              </el-button>
            </div>

            <!-- 实时性能监控 -->
            <el-row :gutter="20" style="margin-bottom: 20px;">
              <el-col :span="8">
                <el-card>
                  <div slot="header">
                    <span>CPU使用率</span>
                  </div>
                  <div class="performance-metric">
                    <div class="metric-value">{{ (monitoringData.cpu_percent || 0).toFixed(1) }}%</div>
                    <el-progress 
                      :percentage="monitoringData.cpu_percent || 0" 
                      :color="getProgressColor(monitoringData.cpu_percent)"
                    ></el-progress>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card>
                  <div slot="header">
                    <span>内存使用率</span>
                  </div>
                  <div class="performance-metric">
                    <div class="metric-value">{{ (monitoringData.memory_percent || 0).toFixed(1) }}%</div>
                    <el-progress 
                      :percentage="monitoringData.memory_percent || 0" 
                      :color="getProgressColor(monitoringData.memory_percent)"
                    ></el-progress>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card>
                  <div slot="header">
                    <span>磁盘使用率</span>
                  </div>
                  <div class="performance-metric">
                    <div class="metric-value">{{ (monitoringData.disk_percent || 0).toFixed(1) }}%</div>
                    <el-progress 
                      :percentage="monitoringData.disk_percent || 0" 
                      :color="getProgressColor(monitoringData.disk_percent)"
                    ></el-progress>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 性能趋势图表 -->
            <el-row :gutter="20" style="margin-bottom: 20px;">
              <el-col :span="24">
                <el-card>
                  <div slot="header">
                    <span>性能趋势图</span>
                    <el-button-group style="float: right;">
                      <el-button size="mini" :type="timeRange === '1h' ? 'primary' : ''" @click="setTimeRange('1h')">1小时</el-button>
                      <el-button size="mini" :type="timeRange === '6h' ? 'primary' : ''" @click="setTimeRange('6h')">6小时</el-button>
                      <el-button size="mini" :type="timeRange === '24h' ? 'primary' : ''" @click="setTimeRange('24h')">24小时</el-button>
                    </el-button-group>
                  </div>
                  <div id="performanceChart" style="height: 400px;"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 服务状态详情 -->
            <el-row :gutter="20">
              <el-col :span="12">
                <el-card>
                  <div slot="header">
                    <span>邮件服务状态</span>
                  </div>
                  <div class="service-details">
                    <div 
                      v-for="service in mailServices" 
                      :key="service.name"
                      class="service-detail-item"
                    >
                      <div class="service-info">
                        <span class="service-name">{{ service.display_name }}</span>
                        <span class="service-description">{{ service.description }}</span>
                      </div>
                      <div class="service-status">
                        <el-tag 
                          :type="service.status === 'running' ? 'success' : 'danger'"
                          size="small"
                        >
                          {{ service.status === 'running' ? '运行中' : '已停止' }}
                        </el-tag>
                        <el-button 
                          size="mini" 
                          :type="service.status === 'running' ? 'warning' : 'success'"
                          @click="toggleService(service)"
                        >
                          {{ service.status === 'running' ? '停止' : '启动' }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <div slot="header">
                    <span>系统信息</span>
                  </div>
                  <div class="system-info">
                    <div class="info-item">
                      <span class="info-label">系统版本:</span>
                      <span class="info-value">{{ systemInfo.os_version || 'Ubuntu 20.04 LTS' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">运行时间:</span>
                      <span class="info-value">{{ systemInfo.uptime || '0天0小时' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">负载平均:</span>
                      <span class="info-value">{{ systemInfo.load_average || '0.00, 0.00, 0.00' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">网络连接:</span>
                      <span class="info-value">{{ systemInfo.network_connections || '0' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">邮件队列:</span>
                      <span class="info-value">{{ systemInfo.mail_queue || '0' }}</span>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 系统设置 -->
          <div v-if="activeMenu === 'settings'" class="settings">
            <div class="page-header">
              <h3>系统设置</h3>
            </div>

            <el-card>
              <el-form :model="systemSettings" label-width="120px">
                <el-form-item label="系统名称">
                  <el-input v-model="systemSettings.systemName"></el-input>
                </el-form-item>
                <el-form-item label="默认配额">
                  <el-input-number v-model="systemSettings.defaultQuota" :min="100" :max="10240"></el-input-number>
                  <span style="margin-left: 10px;">MB</span>
                </el-form-item>
                <el-form-item label="启用注册">
                  <el-switch v-model="systemSettings.enableRegistration"></el-switch>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveSettings">保存设置</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </el-main>
      </el-container>
    </div>

    <!-- 添加用户对话框 -->
    <el-dialog title="添加用户" :visible.sync="addUserDialogVisible" width="500px">
      <el-form :model="newUser" :rules="userRules" ref="userForm" label-width="80px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="newUser.email" placeholder="user@example.com"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="newUser.password" type="password" show-password></el-input>
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="newUser.name" placeholder="用户姓名"></el-input>
        </el-form-item>
        <el-form-item label="配额">
          <el-input-number v-model="newUser.quota" :min="100" :max="10240"></el-input-number>
          <span style="margin-left: 10px;">MB</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="newUser.enabled"></el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addUser" :loading="addUserLoading">确定</el-button>
      </div>
    </el-dialog>

    <!-- 垃圾邮件测试对话框 -->
    <el-dialog title="垃圾邮件检测测试" :visible.sync="spamTestDialogVisible" width="600px">
      <el-form :model="testEmail" label-width="80px">
        <el-form-item label="发件人">
          <el-input v-model="testEmail.from" placeholder="sender@example.com"></el-input>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="testEmail.subject" placeholder="邮件主题"></el-input>
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="testEmail.body" type="textarea" :rows="5" placeholder="邮件内容"></el-input>
        </el-form-item>
      </el-form>
      <div v-if="spamTestResult" class="test-result">
        <h4>检测结果:</h4>
        <p><strong>是否垃圾邮件:</strong> {{ spamTestResult.is_spam ? '是' : '否' }}</p>
        <p><strong>置信度:</strong> {{ (spamTestResult.confidence * 100).toFixed(2) }}%</p>
        <p><strong>检测方法:</strong> {{ spamTestResult.method }}</p>
      </div>
      <div slot="footer">
        <el-button @click="spamTestDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="runSpamTest" :loading="spamTestLoading">开始检测</el-button>
      </div>
    </el-dialog>

    <!-- 添加域名对话框 -->
    <el-dialog title="添加域名" :visible.sync="addDomainDialogVisible" width="500px">
      <el-form :model="newDomain" :rules="domainRules" ref="domainForm" label-width="80px">
        <el-form-item label="域名" prop="domain">
          <el-input v-model="newDomain.domain" placeholder="example.com"></el-input>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newDomain.description" placeholder="域名描述"></el-input>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="newDomain.active"></el-switch>
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="addDomainDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addDomain" :loading="addDomainLoading">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import * as echarts from 'echarts'

export default {
  name: 'App',
  data() {
    return {
      // 认证状态
      isAuthenticated: false,
      currentUser: {},
      
      // 登录表单
      loginForm: {
        email: '',
        password: ''
      },
      loginRules: {
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
        ]
      },
      loginLoading: false,
      
      // 导航
      activeMenu: 'dashboard',
      unreadCount: 0,
      
      // 统计数据
      stats: {
        users: { total: 0, active: 0 },
        mails: { today: 0, total: 0 },
        system: { cpu_percent: 0, memory_percent: 0, disk_percent: 0 },
        services: []
      },
      
      // 用户管理
      users: [],
      usersLoading: false,
      userSearch: '',
      currentPage: 1,
      pageSize: 10,
      totalUsers: 0,
      
      // 添加用户对话框
      addUserDialogVisible: false,
      newUser: {
        email: '',
        password: '',
        name: '',
        quota: 1024,
        enabled: true
      },
      userRules: {
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
        ]
      },
      addUserLoading: false,
      
      // AI功能
      aiStats: {
        total_predictions: 0,
        spam_detected: 0,
        ham_detected: 0
      },
      
      // 垃圾邮件测试
      spamTestDialogVisible: false,
      testEmail: {
        from: '',
        subject: '',
        body: ''
      },
      spamTestResult: null,
      spamTestLoading: false,
      
      // 邮件日志
      mailLogs: [],
      logsLoading: false,
      logFilter: '',
      
      // 域名管理
      domains: [],
      domainsLoading: false,
      domainSearch: '',
      domainCurrentPage: 1,
      domainPageSize: 10,
      totalDomains: 0,
      
      // 添加域名对话框
      addDomainDialogVisible: false,
      newDomain: {
        domain: '',
        description: '',
        active: true
      },
      domainRules: {
        domain: [
          { required: true, message: '请输入域名', trigger: 'blur' },
          { pattern: /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/, message: '请输入正确的域名格式', trigger: 'blur' }
        ]
      },
      addDomainLoading: false,
      
      // 系统监控
      monitoringData: {
        cpu_percent: 0,
        memory_percent: 0,
        disk_percent: 0
      },
      timeRange: '1h',
      mailServices: [
        {
          name: 'postfix',
          display_name: 'Postfix (SMTP)',
          description: 'SMTP邮件发送服务',
          status: 'running'
        },
        {
          name: 'dovecot',
          display_name: 'Dovecot (IMAP/POP3)',
          description: 'IMAP/POP3邮件接收服务',
          status: 'running'
        },
        {
          name: 'spamassassin',
          display_name: 'SpamAssassin',
          description: '垃圾邮件过滤服务',
          status: 'running'
        },
        {
          name: 'clamav',
          display_name: 'ClamAV',
          description: '病毒扫描服务',
          status: 'running'
        }
      ],
      systemInfo: {
        os_version: 'Ubuntu 20.04 LTS',
        uptime: '0天0小时',
        load_average: '0.00, 0.00, 0.00',
        network_connections: '0',
        mail_queue: '0'
      },
      
      // 系统设置
      systemSettings: {
        systemName: '企业级邮箱系统',
        defaultQuota: 1024,
        enableRegistration: true
      },
      
      // 图表实例
      systemChart: null,
      performanceChart: null
    }
  },
  
  mounted() {
    this.checkAuth()
    this.initCharts()
    if (this.isAuthenticated) {
      this.loadDashboardData()
    }
  },
  
  methods: {
    // 认证相关
    checkAuth() {
      const token = localStorage.getItem('access_token')
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        this.isAuthenticated = true
        this.getCurrentUser()
      }
    },
    
    async getCurrentUser() {
      try {
        const response = await axios.get('/api/auth/me')
        this.currentUser = response.data
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.logout()
      }
    },
    
    async handleLogin() {
      this.$refs.loginForm.validate(async (valid) => {
        if (valid) {
          this.loginLoading = true
          try {
            const response = await axios.post('/api/auth/login', this.loginForm)
            const { access_token, user } = response.data
            
            localStorage.setItem('access_token', access_token)
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
            
            this.isAuthenticated = true
            this.currentUser = user
            this.loadDashboardData()
            
            this.$message.success('登录成功')
          } catch (error) {
            this.$message.error(error.response?.data?.message || '登录失败')
          } finally {
            this.loginLoading = false
          }
        }
      })
    },
    
    logout() {
      localStorage.removeItem('access_token')
      delete axios.defaults.headers.common['Authorization']
      this.isAuthenticated = false
      this.currentUser = {}
      this.activeMenu = 'dashboard'
    },
    
    // 导航相关
    handleMenuSelect(index) {
      this.activeMenu = index
      
      switch(index) {
        case 'users':
          this.loadUsers()
          break
        case 'domains':
          this.loadDomains()
          break
        case 'ai-features':
          this.loadAIStats()
          break
        case 'mail-logs':
          this.loadMailLogs()
          break
        case 'monitoring':
          this.loadMonitoringData()
          break
        case 'settings':
          this.loadSettings()
          break
      }
    },
    
    handleUserCommand(command) {
      switch(command) {
        case 'logout':
          this.logout()
          break
        case 'profile':
          this.$message.info('个人资料功能开发中')
          break
        case 'settings':
          this.activeMenu = 'settings'
          this.loadSettings()
          break
      }
    },
    
    showNotifications() {
      this.$message.info('通知功能开发中')
    },
    
    // 数据加载相关
    async loadDashboardData() {
      try {
        const response = await axios.get('/api/stats')
        this.stats = response.data
        this.updateCharts()
      } catch (error) {
        console.error('加载仪表盘数据失败:', error)
      }
    },
    
    async refreshStats() {
      await this.loadDashboardData()
      this.$message.success('数据已刷新')
    },
    
    // 用户管理相关
    async loadUsers() {
      this.usersLoading = true
      try {
        const params = {
          page: this.currentPage,
          per_page: this.pageSize,
          search: this.userSearch
        }
        const response = await axios.get('/api/users', { params })
        this.users = response.data.users
        this.totalUsers = response.data.total
      } catch (error) {
        this.$message.error('加载用户列表失败')
      } finally {
        this.usersLoading = false
      }
    },
    
    searchUsers() {
      this.currentPage = 1
      this.loadUsers()
    },
    
    handleSizeChange(val) {
      this.pageSize = val
      this.loadUsers()
    },
    
    handleCurrentChange(val) {
      this.currentPage = val
      this.loadUsers()
    },
    
    showAddUserDialog() {
      this.addUserDialogVisible = true
      this.newUser = {
        email: '',
        password: '',
        name: '',
        quota: 1024,
        enabled: true
      }
    },
    
    async addUser() {
      this.$refs.userForm.validate(async (valid) => {
        if (valid) {
          this.addUserLoading = true
          try {
            await axios.post('/api/users', this.newUser)
            this.$message.success('用户添加成功')
            this.addUserDialogVisible = false
            this.loadUsers()
          } catch (error) {
            this.$message.error(error.response?.data?.message || '添加用户失败')
          } finally {
            this.addUserLoading = false
          }
        }
      })
    },
    
    editUser(user) {
      this.$message.info('编辑用户功能开发中')
    },
    
    async toggleUserStatus(user) {
      try {
        await axios.put(`/api/users/${user.id}`, {
          enabled: !user.enabled
        })
        user.enabled = !user.enabled
        this.$message.success(`用户已${user.enabled ? '启用' : '禁用'}`)
      } catch (error) {
        this.$message.error('操作失败')
      }
    },
    
    async deleteUser(user) {
      this.$confirm('确定要删除这个用户吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`/api/users/${user.id}`)
          this.$message.success('用户删除成功')
          this.loadUsers()
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    
    // AI功能相关
    async loadAIStats() {
      try {
        const response = await axios.get('/api/ai/stats')
        this.aiStats = response.data
      } catch (error) {
        console.error('加载AI统计失败:', error)
      }
    },
    
    testSpamDetection() {
      this.spamTestDialogVisible = true
      this.testEmail = {
        from: 'test@example.com',
        subject: 'Test Email',
        body: 'This is a test email content.'
      }
      this.spamTestResult = null
    },
    
    async runSpamTest() {
      this.spamTestLoading = true
      try {
        const response = await axios.post('/api/ai/spam-test', this.testEmail)
        this.spamTestResult = response.data
      } catch (error) {
        this.$message.error('检测失败')
      } finally {
        this.spamTestLoading = false
      }
    },
    
    // 邮件日志相关
    async loadMailLogs() {
      this.logsLoading = true
      try {
        const params = {}
        if (this.logFilter) {
          params.status = this.logFilter
        }
        const response = await axios.get('/api/mail-logs', { params })
        this.mailLogs = response.data
      } catch (error) {
        this.$message.error('加载邮件日志失败')
      } finally {
        this.logsLoading = false
      }
    },
    
    getStatusType(status) {
      const types = {
        'received': 'success',
        'spam': 'warning',
        'blocked': 'danger'
      }
      return types[status] || 'info'
    },
    
    getStatusText(status) {
      const texts = {
        'received': '已接收',
        'spam': '垃圾邮件',
        'blocked': '已阻止'
      }
      return texts[status] || status
    },
    
    // 系统设置相关
    async loadSettings() {
      try {
        const response = await axios.get('/api/settings')
        this.systemSettings = response.data
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    },
    
    async saveSettings() {
      try {
        await axios.put('/api/settings', this.systemSettings)
        this.$message.success('设置保存成功')
      } catch (error) {
        this.$message.error('保存失败')
      }
    },
    
    // 工具方法
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    },
    
    // 图表相关
    initCharts() {
      this.$nextTick(() => {
        if (document.getElementById('systemChart')) {
          this.systemChart = echarts.init(document.getElementById('systemChart'))
        }
        if (document.getElementById('performanceChart')) {
          this.performanceChart = echarts.init(document.getElementById('performanceChart'))
        }
      })
    },
    
    updateCharts() {
      if (this.systemChart && this.stats.system) {
        const option = {
          title: {
            text: '系统资源使用情况'
          },
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['CPU', '内存', '磁盘']
          },
          xAxis: {
            type: 'category',
            data: ['当前']
          },
          yAxis: {
            type: 'value',
            max: 100
          },
          series: [
            {
              name: 'CPU',
              type: 'bar',
              data: [this.stats.system.cpu_percent || 0]
            },
            {
              name: '内存',
              type: 'bar',
              data: [this.stats.system.memory_percent || 0]
            },
            {
              name: '磁盘',
              type: 'bar',
              data: [this.stats.system.disk_percent || 0]
            }
          ]
        }
        this.systemChart.setOption(option)
      }
    },
    
    // 域名管理相关方法
    async loadDomains() {
      this.domainsLoading = true
      try {
        const params = {
          page: this.domainCurrentPage,
          per_page: this.domainPageSize,
          search: this.domainSearch
        }
        const response = await axios.get('/api/domains', { params })
        this.domains = response.data.domains || []
        this.totalDomains = response.data.total || 0
      } catch (error) {
        this.$message.error('加载域名列表失败')
      } finally {
        this.domainsLoading = false
      }
    },
    
    searchDomains() {
      this.domainCurrentPage = 1
      this.loadDomains()
    },
    
    handleDomainSizeChange(val) {
      this.domainPageSize = val
      this.loadDomains()
    },
    
    handleDomainCurrentChange(val) {
      this.domainCurrentPage = val
      this.loadDomains()
    },
    
    showAddDomainDialog() {
      this.addDomainDialogVisible = true
      this.newDomain = {
        domain: '',
        description: '',
        active: true
      }
    },
    
    async addDomain() {
      this.$refs.domainForm.validate(async (valid) => {
        if (valid) {
          this.addDomainLoading = true
          try {
            await axios.post('/api/domains', this.newDomain)
            this.$message.success('域名添加成功')
            this.addDomainDialogVisible = false
            this.loadDomains()
          } catch (error) {
            this.$message.error(error.response?.data?.message || '添加域名失败')
          } finally {
            this.addDomainLoading = false
          }
        }
      })
    },
    
    editDomain(domain) {
      this.$message.info('编辑域名功能开发中')
    },
    
    async toggleDomainStatus(domain) {
      try {
        await axios.put(`/api/domains/${domain.id}`, {
          active: !domain.active
        })
        domain.active = !domain.active
        this.$message.success(`域名已${domain.active ? '启用' : '停用'}`)
      } catch (error) {
        this.$message.error('操作失败')
      }
    },
    
    async deleteDomain(domain) {
      this.$confirm('确定要删除这个域名吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`/api/domains/${domain.id}`)
          this.$message.success('域名删除成功')
          this.loadDomains()
        } catch (error) {
          this.$message.error('删除失败')
        }
      })
    },
    
    // 系统监控相关方法
    async loadMonitoringData() {
      try {
        const response = await axios.get('/api/monitoring/system')
        this.monitoringData = response.data
        this.updatePerformanceChart()
      } catch (error) {
        console.error('加载监控数据失败:', error)
      }
    },
    
    async refreshMonitoringData() {
      await this.loadMonitoringData()
      await this.loadSystemInfo()
      await this.loadServiceStatus()
      this.$message.success('监控数据已刷新')
    },
    
    async loadSystemInfo() {
      try {
        const response = await axios.get('/api/monitoring/system-info')
        this.systemInfo = response.data
      } catch (error) {
        console.error('加载系统信息失败:', error)
      }
    },
    
    async loadServiceStatus() {
      try {
        const response = await axios.get('/api/monitoring/services')
        this.mailServices = response.data.services || this.mailServices
      } catch (error) {
        console.error('加载服务状态失败:', error)
      }
    },
    
    getProgressColor(percentage) {
      if (percentage < 50) {
        return '#67c23a'
      } else if (percentage < 80) {
        return '#e6a23c'
      } else {
        return '#f56c6c'
      }
    },
    
    setTimeRange(range) {
      this.timeRange = range
      this.updatePerformanceChart()
    },
    
    async toggleService(service) {
      try {
        const action = service.status === 'running' ? 'stop' : 'start'
        await axios.post(`/api/monitoring/services/${service.name}/${action}`)
        service.status = service.status === 'running' ? 'stopped' : 'running'
        this.$message.success(`服务${action === 'start' ? '启动' : '停止'}成功`)
      } catch (error) {
        this.$message.error('服务操作失败')
      }
    },
    
    updatePerformanceChart() {
      if (this.performanceChart) {
        // 模拟性能数据
        const timeLabels = []
        const cpuData = []
        const memoryData = []
        const diskData = []
        
        // 根据时间范围生成模拟数据
        const points = this.timeRange === '1h' ? 12 : this.timeRange === '6h' ? 24 : 48
        
        for (let i = 0; i < points; i++) {
          const now = new Date()
          const time = new Date(now.getTime() - (points - i) * (this.timeRange === '1h' ? 5 : this.timeRange === '6h' ? 15 : 30) * 60000)
          timeLabels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
          
          // 模拟数据波动
          cpuData.push(Math.max(0, Math.min(100, (this.monitoringData.cpu_percent || 0) + (Math.random() - 0.5) * 20)))
          memoryData.push(Math.max(0, Math.min(100, (this.monitoringData.memory_percent || 0) + (Math.random() - 0.5) * 15)))
          diskData.push(Math.max(0, Math.min(100, (this.monitoringData.disk_percent || 0) + (Math.random() - 0.5) * 10)))
        }
        
        const option = {
          title: {
            text: `性能趋势图 (${this.timeRange})`
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross'
            }
          },
          legend: {
            data: ['CPU', '内存', '磁盘']
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: timeLabels
          },
          yAxis: {
            type: 'value',
            max: 100,
            axisLabel: {
              formatter: '{value}%'
            }
          },
          series: [
            {
              name: 'CPU',
              type: 'line',
              smooth: true,
              data: cpuData,
              itemStyle: {
                color: '#409eff'
              }
            },
            {
              name: '内存',
              type: 'line',
              smooth: true,
              data: memoryData,
              itemStyle: {
                color: '#67c23a'
              }
            },
            {
              name: '磁盘',
              type: 'line',
              smooth: true,
              data: diskData,
              itemStyle: {
                color: '#e6a23c'
              }
            }
          ]
        }
        
        this.performanceChart.setOption(option)
      }
    }
  }
}
</script>

<style scoped>
/* 全局样式 */
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  margin: 0;
  padding: 0;
}

/* 登录页面样式 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  color: #909399;
  margin: 0;
}

.login-form .el-form-item {
  margin-bottom: 25px;
}

/* 主应用界面样式 */
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.header-left h3 {
  margin: 0;
  color: #303133;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #606266;
}

.username {
  font-size: 14px;
}

.app-sidebar {
  background: #304156;
  overflow-x: hidden;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
  border-bottom: 1px solid #263445;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.sidebar-menu .el-menu-item i {
  margin-right: 8px;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  color: #303133;
  font-weight: 500;
}

/* 仪表盘样式 */
.dashboard {
  max-width: 1200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.users {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.mails {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.system {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.charts-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.chart-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.services-status {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.service-name {
  font-weight: 500;
  color: #303133;
}

/* 用户管理样式 */
.users-management {
  max-width: 1200px;
}

.table-toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* AI功能样式 */
.ai-features {
  max-width: 1200px;
}

.ai-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.ai-stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.ai-stat-item:last-child {
  border-bottom: none;
}

.ai-stat-item .label {
  color: #606266;
  font-size: 14px;
}

.ai-stat-item .value {
  color: #303133;
  font-weight: 500;
}

.ai-feature-item {
  text-align: center;
  padding: 20px;
}

.ai-feature-item p {
  color: #606266;
  margin-bottom: 20px;
  line-height: 1.6;
}

/* 域名管理样式 */
.domains-management {
  max-width: 1200px;
}

/* 系统监控样式 */
.monitoring {
  max-width: 1200px;
}

.performance-metric {
  text-align: center;
  padding: 20px 0;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 15px;
}

.service-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.service-detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.service-info {
  flex: 1;
}

.service-name {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
  display: block;
  margin-bottom: 5px;
}

.service-description {
  color: #606266;
  font-size: 14px;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #606266;
  font-weight: 500;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-weight: 600;
  font-size: 14px;
}

/* 邮件日志样式 */
.mail-logs {
  max-width: 1200px;
}

/* 系统设置样式 */
.settings {
  max-width: 800px;
}

/* 对话框样式 */
.test-result {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #409eff;
}

.test-result h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
}

.test-result p {
  margin: 8px 0;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-sidebar {
    width: 200px !important;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .login-card {
    width: 90%;
    margin: 0 20px;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 动画效果 */
.stat-card {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.chart-card {
  transition: box-shadow 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
</style>