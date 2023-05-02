# Feishu_GPT_Summarization
This project extracts all URLs from a given input text, pre-processed with tagged URLs. Utilizing the power of GPT, the content is first summarized, and then the final output is sent to Lark/Feishu for further use.

## 服务器设置
该项目从带有标注URL的给定输入文本中提取所有URL。通过利用GPT的能力，首先对内容进行概括，然后将最终输出发送到飞书/Lark以供进一步使用。

在使用该功能的时候需要部署一个简单的 Flask 应用，用来接受来自 Webhook 的 POST 请求，并将其中的文本数据返回。

首先，你需要安装 Flask，可以使用 pip 命令来安装：
```
pip install Flask
```
我们在app.py文件中创建了一个 Flask 应用，并定义了一个名为 receive_webhook 的函数，用于处理来自 Webhook 的 POST 请求。该函数从请求中获取数据，并直接将其返回。

在主程序中，我们使用 Flask 的 run() 方法运行应用。如果你直接运行 python app.py，则 Flask 会将应用运行在默认的 5000 端口上。而为了接受从飞书传过来的信息，我们需要用要使用 Gunicorn 来部署 Flask 应用，请按照以下步骤操作：

1. 在您的虚拟环境中，使用以下命令安装 Gunicorn：
```
pip install gunicorn
```
2. 使用 Gunicorn 运行 Flask 应用，确保您已在虚拟环境中激活并在 Flask 应用目录中，然后使用以下命令运行 Gunicorn：
```
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```
这将启动一个绑定到所有 IP 地址 (0.0.0.0) 的 Gunicorn 服务器，监听端口 8080，并运行 4 个工作进程。您可以根据需要调整端口和工作进程数量。
3. 随后我们需要确保在后台运行 Gunicorn 服务器，并将输出重定向到一个日志文件以便于查看和调试。此外，我们还需要设置请求超时，以处理可能需要较长时间的操作。因此，我们需要使用以下命令：
```
nohup gunicorn -w 4 -b 0.0.0.0:8084 app:app --timeout 1200 > output.log 2>&1 &
```
这条命令的作用如下：
  * nohup 命令使 Gunicorn 服务器在后台运行，即使您关闭了终端窗口，服务器也会继续运行。
  * -w 4 参数设置了 4 个工作进程，以处理更多并发请求。
  * -b 0.0.0.0:8084 参数设置了服务器监听的 IP 地址和端口。在这里，我们选择了端口 8084，您可以根据需要进行调整。
  * app:app 指定了运行的 Flask 应用。
  * --timeout 1200 参数设置了请求超时时间为 1200 秒，以处理可能需要较长时间的操作。
  * \> output.log 2>&1 将服务器的标准输出和错误输出重定向到名为 "output.log" 的文件中，方便查看和调试。
  * & 符号使命令在后台运行，不会阻塞当前终端。
