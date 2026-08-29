// fp_scanner —— aififteen Hunter 高性能指纹组件（Go）。
//
// 方案定位：端口/组件识别等高并发 CPU 密集场景用 Go，编译为二进制后
// 由 Python 侧 engine/fingerprint/__init__.py 通过 subprocess 调用。
// 本骨架用纯标准库实现（探活+标题+webserver+组件指纹+常见端点发现），
// 零第三方依赖，go build 即可：
//
//	cd engine/golang/fp_scanner && go build -o ../bin/fp_scanner .
//	Windows: go build -o ../bin/fp_scanner.exe .
//
// 输出 JSON：{url, host, scheme, port, status, title, webserver, techs, paths}
// Python 侧解析失败或二进制缺失时自动降级 py_fp（Python 兜底实现）。
package main

import (
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

type Result struct {
	URL       string   `json:"url"`
	Host      string   `json:"host"`
	Scheme    string   `json:"scheme"`
	Port      int      `json:"port"`
	Status    int      `json:"status"`
	Title     string   `json:"title"`
	Webserver string   `json:"webserver"`
	Techs     []string `json:"techs"`
	Paths     []string `json:"paths"`
}

var titleRe = regexp.MustCompile(`(?is)<title[^>]*>(.*?)</title>`)

// (tech 名, 检查位置, 匹配串)：与 py_fp.py 保持同源规则
var techRules = []struct{ name, where, needle string }{
	{"php", "header", "x-powered-by:php"},
	{"asp.net", "header", "x-powered-by:asp.net"},
	{"express", "header", "x-powered-by:express"},
	{"php", "header", "set-cookie:phpsessid"},
	{"jsp", "header", "set-cookie:jsessionid"},
	{"laravel", "header", "set-cookie:laravel_session"},
	{"django", "header", "set-cookie:csrftoken"},
	{"shiro", "header", "set-cookie:rememberme"},
	{"nginx", "server", "nginx"},
	{"apache", "server", "apache"},
	{"iis", "server", "microsoft-iis"},
	{"tomcat", "server", "tomcat"},
	{"openresty", "server", "openresty"},
	{"caddy", "server", "caddy"},
	{"jquery", "body", "jquery"},
	{"vue", "body", "vue"},
	{"react", "body", "react"},
	{"element-plus", "body", "element-plus"},
	{"bootstrap", "body", "bootstrap"},
	{"webpack", "body", "webpack"},
	{"wordpress", "body", "wp-content"},
	{"drupal", "body", "drupal"},
	{"joomla", "body", "joomla"},
	{"discuz", "body", "discuz"},
	{"dedecms", "body", "dedecms"},
	{"spring", "body", "org.springframework"},
	{"swagger", "body", "swagger-ui"},
}

var discoverPaths = []string{
	"/robots.txt", "/sitemap.xml", "/admin/", "/login", "/api",
	"/swagger-ui.html", "/swagger.json", "/actuator", "/index.php",
	"/admin/login", "/api/v1", "/druid/index.html",
}

func client(timeout time.Duration) *http.Client {
	return &http.Client{
		Timeout: timeout,
		Transport: &http.Transport{
			TLSClientConfig:   &tls.Config{InsecureSkipVerify: true}, // nosec G402 扫描器需接受自签
			DisableKeepAlives: false,
		},
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 5 {
				return fmt.Errorf("too many redirects")
			}
			return nil
		},
	}
}

func fetch(c *http.Client, url string) (int, http.Header, []byte) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return 0, nil, nil
	}
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) aififteen-fp")
	resp, err := c.Do(req)
	if err != nil {
		return 0, nil, nil
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	return resp.StatusCode, resp.Header, body
}

func main() {
	rawURL := flag.String("url", "", "target url")
	timeout := flag.Int("timeout", 20, "seconds")
	flag.Parse()
	if *rawURL == "" {
		fmt.Println("{}")
		return
	}

	u, err := url.Parse(strings.TrimSpace(*rawURL))
	if err != nil || u.Host == "" {
		fmt.Println("{}")
		return
	}
	scheme := "http"
	if u.Scheme == "https" {
		scheme = "https"
	}
	port := 80
	if scheme == "https" {
		port = 443
	}
	if p := u.Port(); p != "" {
		fmt.Sscanf(p, "%d", &port)
	}

	c := client(time.Duration(*timeout) * time.Second)
	status, header, body := fetch(c, scheme+"://"+u.Host)
	if status == 0 {
		fmt.Println("{}")
		return
	}

	res := Result{URL: scheme + "://" + u.Host, Host: u.Host,
		Scheme: scheme, Port: port, Status: status, Techs: []string{},
		Paths: []string{}}

	if m := titleRe.FindSubmatch(body); len(m) > 1 {
		res.Title = strings.TrimSpace(regexp.MustCompile(`\s+`).
			ReplaceAllString(string(m[1]), " "))
		if len(res.Title) > 120 {
			res.Title = res.Title[:120]
		}
	}
	res.Webserver = header.Get("Server")
	if idx := strings.Index(res.Webserver, "/"); idx > 0 {
		res.Webserver = res.Webserver[:idx]
	}

	lowerBody := strings.ToLower(string(body))
	var headerPairs []string
	for k, vs := range header {
		for _, v := range vs {
			headerPairs = append(headerPairs, strings.ToLower(k)+":"+strings.ToLower(v))
		}
	}
	for _, r := range techRules {
		hit := false
		switch r.where {
		case "header":
			for _, h := range headerPairs {
				if strings.Contains(h, r.needle) {
					hit = true
				}
			}
		case "server":
			hit = strings.Contains(strings.ToLower(res.Webserver), r.needle)
		case "body":
			hit = strings.Contains(lowerBody, r.needle)
		}
		if hit {
			res.Techs = append(res.Techs, r.name)
		}
	}

	// 常见端点发现（并发 8）
	sem := make(chan struct{}, 8)
	done := make(chan string, len(discoverPaths))
	for _, p := range discoverPaths {
		go func(p string) {
			sem <- struct{}{}
			defer func() { <-sem }()
			st, _, _ := fetch(c, res.URL+p)
			if st == 200 || st == 401 || st == 403 {
				done <- p
			}
		}(p)
	}
	for range discoverPaths {
		if p, ok := <-done; ok && p != "" {
			res.Paths = append(res.Paths, p)
		}
	}

	out, _ := json.Marshal(res)
	fmt.Println(string(out))
}
