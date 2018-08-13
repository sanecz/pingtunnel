# pingtunnel [![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

> a tiny TCP over ICMP tunnel in pure python (no deps required)

## Usage

    usage: Needs to be runned as root (use of raw sockets)
      Client side: pptunnel -p <proxy_host> -lp <proxy_port> -dh <dest_host> -dp <dest_port>
      Proxy side: pptunnel -s
    
    pptunnel, python ping tunnel, send your tcp traffic over icmp
    
    optional arguments:
      -h, --help            show this help message and exit
      -s, --server          Set proxy mode
      -p PROXY_HOST, --proxy_host PROXY_HOST
                            Host on which the proxy is running
      -lh LOCAL_HOST, --local_host LOCAL_HOST
                            (local) Listen ip for incomming TCP
                            connections,default 127.0.0.1
      -lp LOCAL_PORT, --local_port LOCAL_PORT
                            (local) Listen port for incomming TCP connections
      -dh DESTINATION_HOST, --destination_host DESTINATION_HOST
                            Specifies the remote host to send your TCP connection
      -dp DESTINATION_PORT, --destination_port DESTINATION_PORT
                            Specifies the remote port to send your TCP connection



## Known bugs/issues/TODOs
   - Bad thread management
   - Bad socket cleaning
   - Doc
   
