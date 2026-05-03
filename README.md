# 飞书多维表格鉴权插件

通过飞书多维表格的员工记录，在 Dify Chatflow/Workflow 中实现用户权限验证。

## 功能

- 用 `sys.user_id`（或任意输入变量）匹配多维表格中的工号列
- 返回 `result`（yes/no）、`permission_value`（权限列值）、`message`（结果描述）
- 每个工具节点独立配置飞书应用凭证，支持多应用场景
- 支持下游 IF/ELSE 条件分支节点根据权限值进行多级路由

---

## 前置准备

### 1. 创建飞书自建应用

1. 进入 [飞书开放平台](https://open.feishu.cn/app) → 创建企业自建应用
2. 记录 `App ID` 和 `App Secret`
3. 开通权限：**云文档** → 「查看、评论、编辑和管理多维表格」或仅读权限 `bitable:app:readonly`
4. 发布应用版本并上线

### 2. 获取多维表格参数

打开飞书多维表格，从 URL 中获取：

```
https://your-company.feishu.cn/base/BascXXXXXXXX?table=tblXXXXXXXX&view=vewXXXXXXXX
                                     ↑ app_token        ↑ table_id        ↑ view_id（可选）
```

### 3. 将应用加入多维表格

多维表格右上角 → **分享** → 邀请刚创建的飞书应用，赋予「查看」权限。

---

## 安装插件

### 方式一：上传插件包

下载最新 [.difypkg](https://github.com/JaikenWong/DifyAuthByFeishuBitable/releases) 发布包，在 Dify 控制台 → 插件 → 上传插件包。

### 方式二：远程调试（开发环境）

```bash
cd dify-file-plugin
cp .env.example .env
# 填写 .env 中的 REMOTE_INSTALL_KEY（从 Dify 控制台获取）

pip install -r requirements.txt
python -m main
```

---

## 在 Chatflow 中使用

### 推荐流程

```
[开始节点]
    ↓
[工具节点: Auth Check]
    ↓
[IF/ELSE 条件分支]
  ├─ result == yes ──→ [正常业务节点]
  │                        ↓
  │              （可再按 permission_value 分支）
  └─ ELSE ──→ [直接回复: 无权限提示]
```

### 工具节点参数配置

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `app_id` | ✅ | 飞书自建应用 App ID | `cli_a96937074338dbc6` |
| `app_secret` | ✅ | 飞书自建应用 App Secret | |
| `user_id` | ✅ | 用户标识，映射 `sys.user_id` 或用户输入变量 | `{{#sys.user_id#}}` |
| `app_token` | ✅ | 多维表格 App Token | `BascXXXXXXXX` |
| `table_id` | ✅ | 数据表 ID | `tblXXXXXXXX` |
| `view_id` | ❌ | 视图 ID，可缩小查询范围 | `vewXXXXXXXX` |
| `employee_col` | ✅ | 用于匹配 user_id 的列名 | `工号` |
| `permission_col` | ❌ | 权限列名，其值输出到 `permission_value` | `角色` |

### 输出变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `result` | string | `"yes"` 表示有权限，`"no"` 表示无权限 |
| `permission_value` | string | `permission_col` 列的值，可用于多级权限分支 |
| `message` | string | 鉴权结果描述 |

### 条件分支配置示例

IF/ELSE 节点：
- **条件**：`auth_check.result` `等于` `yes`
- **IF 分支**：有权限，继续正常业务流程
- **ELSE 分支**：无权限，直接回复拒绝提示

---

## 典型场景示例

### 场景一：仅判断有无权限

- `permission_col` 留空
- 分支条件：`result == yes`

### 场景二：按角色分流

多维表格中有「角色」列，值为 `admin` / `user` / `guest`：

- `permission_col` = `角色`
- 分支1：`permission_value == admin` → 高权限流程
- 分支2：`permission_value == user` → 普通流程
- 分支3：`result == no` → 拒绝

### 场景三：user_id 来自用户输入

开始节点添加输入变量 `employee_id`，工具节点 `user_id` 映射为 `{{#sys.inputs.employee_id#}}`。

---

## 多维表格结构示例

| 工号（employee_col） | 姓名 | 角色（permission_col） | 备注 |
|---|---|---|---|
| U123456 | 张三 | admin | |
| U789012 | 李四 | user | |

`sys.user_id` 的值需与「工号」列的值一致，飞书 user_id 格式通常为 `ou_xxxxxxxx`，请确认 Dify 的 `sys.user_id` 与表格中存储的格式匹配，必要时在表格中存储对应格式的值。

---

## 常见问题

**Q: result 始终为 no？**
检查：① 应用是否已加入多维表格并有读权限 ② `employee_col` 列名是否与表格完全一致（区分全半角）③ `sys.user_id` 的值格式是否与表格中一致

**Q: permission_value 为空？**
`permission_col` 未填写，或该用户对应行的权限列为空值，均正常。

**Q: 飞书 API 报错 99991661？**
App ID 或 App Secret 配置错误，检查工具节点中的凭证是否正确。

**Q: 飞书 API 报错 99991672？**
应用未开通多维表格读权限（`bitable:app` / `bitable:app:readonly` / `base:record:retrieve`），或未发布上线。
