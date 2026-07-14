# GitHub推送说明

## 前置准备

1. **注册GitHub账号**（已有则跳过）
   访问 https://github.com 注册

2. **创建新仓库**
   - 点击右上角 "+" → "New repository"
   - Repository name 填 `jianshuidun-report`（或你喜欢的名字）
   - **不要勾选** "Add a README file"（空仓库就行）
   - 点击 "Create repository"

3. **生成Personal Access Token**
   - 点击右上角头像 → Settings
   - 左侧菜单底部 → Developer settings
   - Personal access tokens → Tokens (classic)
   - Generate new token → Generate new token (classic)
   - Note 随便填（如 `jianshuidun-push`）
   - Expiration 选 90 days 或 No expiration
   - 勾选 `repo` 权限（第一个大项全勾）
   - 拉到底部 Generate token
   - **复制保存好这个Token**（只显示一次，ghp_开头）

## 推送代码

### Windows用户
双击运行 `推送GitHub.bat`，按提示输入：
- GitHub用户名
- 仓库名称
- Personal Access Token

### Mac/Linux用户
```bash
chmod +x 推送GitHub.sh
./推送GitHub.sh
```

### 手动命令（推荐）
如果你熟悉命令行，直接执行：
```bash
cd jianzao-report
git init
git add .
git commit -m "初始版本: 建税盾建筑经营管理报表系统 MVP v0.1.0"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```
输入你的GitHub用户名和Token即可。

## 推送完成后
访问 `https://github.com/你的用户名/仓库名` 就能看到代码了。

## Token获取步骤图文（简化版）
1. 打开 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. Note: jianzao
4. Select scopes: 勾选 `repo`
5. 点最下面 Generate token
6. 复制生成的 token（ghp_xxxxxxx），妥善保存
