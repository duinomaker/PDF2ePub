using Microsoft.AspNetCore.SignalR.Client;
using System.Diagnostics;
using System.Net;

namespace Pdf2Epub.Worker.Hubs
{
    public class MessageHub
    {
        private readonly string api_url_;
        private readonly HubConnection connection_;
        private readonly HttpClient client_;
        private readonly Guid id_;

        public MessageHub()
        {
            // api_url_ = Environment.GetEnvironmentVariable("API_ENDPOINT");
            api_url_ = "http://localhost:49161";

            client_ = new HttpClient();

            id_ =  Guid.Parse(client_.PostAsync($"{api_url_}/worker", null).Result.Content.ReadAsStringAsync().Result);

            connection_ = new HubConnectionBuilder().WithUrl($"{api_url_}/hub").Build();
            connection_.Closed += async (error) => {
                await Task.Delay(new Random().Next(0, 5) * 1000);
                await connection_.StartAsync();
            };
            connection_.On<string>(
                "ReceiveMessage",
                (task_id) => {
                    var file_id = Guid.Parse(client_.PostAsync($"{api_url_}/{id_}/{task_id}", null).Result.Content.ReadAsStringAsync().Result);
                    var file_path = $"/app/pdf/{file_id}.pdf";

                    var response = client_.GetAsync($"{api_url_}/{file_id}");
                    using (var fs = File.Open(file_path, FileMode.Create))
                    {
                        using (var ms = response.Result.Content.ReadAsStream())
                        {
                            ms.CopyTo(fs);
                        }
                    }

                    var process = new Process() {
                        StartInfo = new ProcessStartInfo() {
                            FileName = "python",
                            Arguments = $"main.py {file_id}.pdf",
                            UseShellExecute = false,
                        }
                    };

                    var callback_output = new DataReceivedEventHandler(
                        (_, e) => {
                            if (!string.IsNullOrEmpty(e.Data))
                            {
                                Console.WriteLine(e.Data);
                            }
                        }
                    );

                    process.StartInfo.RedirectStandardOutput = true;
                    process.OutputDataReceived += callback_output;

                    process.Start();
                    process.BeginOutputReadLine();
                }
            );
        }
    }
}
