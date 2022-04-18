# Pdf2Epub

## 项目简介

一个PDF格式到EPUB电子图书格式的自动转换工具。

## 项目特性

+ 支持本地运行与网站集群化部署；

   - 网站支持动态扩容，可根据需求动态添加后端转换服务器；
   - 后端程序全部使用docker容器化处理，方便部署与维护；
+ 实现了从PDF到EPUB的单个 && 批量转换服务；

   - 作为网站部署时，支持单个文件 && 批量文件上传与转换；
   - 作为本地应用运行时，支持文件夹内指定文件转换 && 所有PDF文件批量转换；
+ 转换时自动保留原有PDF文档的排版样式、标题格式和目录格式；
+ 转换后的文档支持保留原文件名和重新命名；
  
   - 作为网站部署时可在高级设置中指定；
   - 作为本地应用运行时可通过命令行参数指定转换后文件名；
+ 转换过程有完整日志记录，可查看转换完成进度；

   - 网站支持查询历史转换日志，包括但不限于转换时间、转换进度、错误原因等信息；
   
   - 命令行工具会实时显示转换进度与日志信息；
+ 上传支持断点续传，即使网络中断后恢复也可以继续之前的进度；
+ 转换支持历史记忆功能，即系统会保留已经转换完毕的文件，如果发现上传的新文件与历史文件相同，则可直接给出转换后结果，减少资源占用；
+ *(可选的)*支持部署为HTTPS网站，支持启用强制HTTPS，防止网站遭受劫持等攻击；

## 项目架构

项目由四个独立的小项目构成：

```
/Pdf2Epub
    | - Pdf2Epub.Frontend     前端项目
    | - Pdf2Epub.API          网站API项目
    | - Pdf2Epub.Worker		  转换Worker项目
    | - Pdf2Epub.CommandLine  本地命令行工具项目
```

### Pdf2Epub.Frontend

整个网站的前端部分，即所有直接可视的页面都由该项目实现。由Vue.js开发，拥有良好的模块化特性，易于改动与二次开发；部署简单，可部署在任何静态网页服务器中，CDN缓存友好，也可使用对象存储部署，易于实现高并发。

### Pdf2Epub.API

负责前端请求（如用户上传、下载）的响应、转换Worker的管理、转换任务的记录与分配。由.NET开发，经由docker包装，方便部署。该项目直接操作数据库。在当前版本中，数据库使用了本地的sqlite来记录转换任务等信息，是Stateful的组件。但项目本身也支持以Stateless状态使用远程数据库。此如果后台调度、上下行流量非常大以至于调度服务器难以承受的话，可以通过部署多个该项目的实例并搭配均衡负载来实现扩容。根据测试，单个API项目的TPS可轻松达到10000以上，实际中很难遇到需要均衡负载该项目的情况，这也是项目中使用了sqlite的原因。

### Pdf2Epub.Worker

该项目分为两个部分：

+ 由Python编写，负责具体PDF文件的转换。基于PyMuPDF，在保证效率的同时尽可能地支持了更多的功能；

+ 由.NET编写，负责将API程序传入的远程调用请求包装为命令行参数并调用Python编写的程序进行转换，同时也负责了与API程序的沟通（心跳包）；

该项目同样由docker包装，旨在利用docker的特性以实现快速扩容、自动化部署。由于Worker的特性决定了需要不断根据用户的使用量来调整Worker的数量，因此使用容器虚拟化是该项目得以承载高并发的关键。Worker启动后会自动连接到指定的管理端，之后便可接受由API派发的任务。考虑到Worker的成本（位于NAT后的服务器价格更低）与安全性（位于NAT后的服务不能被外界主动连接，不容易被非法请求干扰）问题，该项目假定Worker有可能工作在nat后并单独对这种情况做了特殊兼容。

### Pdf2Epub.CommandLine

该项目为本地命令行项目，可供用户本地运行、测试使用。为了避免版本不兼容导致的安装、执行失败，这里也利用docker进行了封装。

## 如何部署

### 作为本地命令行应用运行

安装镜像：

```shell
docker pull deximy/pdf2epub-cmd
```

……或者自行编译：

```shell
git clone https://github.com/deximy/Pdf2Epub.git
cd Pdf2Epub/Pdf2Epub.CommandLine
docker build -t deximy/pdf2epub-cmd .
```

转换文件/文件夹内所有文件：

```shell
docker run -it --rm -v </path/to/pdf/file>:/app/pdf deximy/pdf2epub-cmd bash -c "python main.py [file_name] [...args]"
```

其中：

+ `</path/to/pdf/file>`为包含待转换的pdf文件的目录，必填；

+ `[file_name]`为待转换的pdf文件的名称，选填，**若不填则默认为批量模式，将转换该目录下所有pdf文件**；

+ `[args]`为本次转换参数，包括：
   ```
   --vertical，当被转换的pdf为垂直排版时使用，当该参数被应用且转换模式为批量模式时，所有文件都被视为垂直排版
   --name，设置转换完成后文件的文件名，当且仅当转换模式为单文件模式时有效
   ```

### 作为网站运行

想完整地运行整个网站需要**依次**部署API端、Worker端、网站前端。

#### API端

安装镜像：

```shell
docker pull deximy/pdf2epub-api
```

……或者自行编译：

```shell
git clone https://github.com/deximy/Pdf2Epub.git
cd Pdf2Epub/Pdf2Epub.API
docker build -t deximy/pdf2epub-api .
```

运行容器：

```shell
docker run -td -p <http-port>:80 deximy/pdf2epub-api -f /dev/null
```

你可以更改`<http-port>`为任何你想要的端口。这代表了API监听的端口。更多参数相关信息（如开启HTTPS等）可以查询https://docs.microsoft.com/en-us/aspnet/core/?view=aspnetcore-6.0与https://docs.docker.com/engine/reference/run/。

#### Worker端

Worker可被同时运行多个以获得更强大的网站并发处理能力。启用多个Worker与启用一个Worker所需代码相同。

安装镜像：

```shell
docker pull deximy/pdf2epub-worker
```

……或者自行编译：

```shell
git clone https://github.com/deximy/Pdf2Epub.git
cd Pdf2Epub/Pdf2Epub.Worker
docker build -t deximy/pdf2epub-worker .
```

运行容器：

```shell
docker run -td -e API_ENDPOINT="<api-endpoint>" deximy/pdf2epub-worker -f /dev/null
```

其中`<api-endpoint>`为某个已经运行了的API端的地址。地址不需要以`/`结尾。必须指定一个地址。目前暂不支持同时作为多个API端的Worker。

#### 网站前端

修改`Pdf2Epub.Frontend/src/apis/api.ts`中的`api_url`为API端的地址，地址不需要以`/`结尾。

编译：

```shell
git clone https://github.com/deximy/Pdf2Epub.git
cd Pdf2Epub/Pdf2Epub.Frontend
yarn
yarn build
```

随后复制`dist`下的所有文件到任意一个Web服务器即可。
