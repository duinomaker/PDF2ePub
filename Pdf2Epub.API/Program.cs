using Microsoft.AspNetCore.Server.Kestrel.Core;
using Pdf2Epub.API.Repositories;
using Pdf2Epub.API.Services;
using tusdotnet;
using tusdotnet.Interfaces;
using tusdotnet.Models;
using tusdotnet.Models.Configuration;
using tusdotnet.Stores;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddCors(
    options => {
        options.AddPolicy(
            name: "AllowAll",
            builder => {
                builder.SetIsOriginAllowed((host) => true);
                builder.AllowAnyMethod();
                builder.AllowAnyHeader();
                builder.AllowCredentials();
                builder.WithExposedHeaders("Location", "Upload-Offset", "Upload-Length");
            }
        );
    }
);

builder.Services.Configure<KestrelServerOptions>(
    options => {
        options.Limits.MaxRequestBodySize = int.MaxValue; // if don't set, the default value will be 30 MB
    }
);
builder.Services.AddSignalR();

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddSingleton(CreateTusConfiguration);
builder.Services.AddHostedService<Pdf2Epub.API.Services.ExpiredFilesCleanupService>();

builder.Services.AddScoped<ConvertTaskRepository>();
builder.Services.AddScoped<WorkerRepository>();

builder.Services.AddScoped<WorkerService>();

var app = builder.Build();

app.UseCors("AllowAll");
var websocket_options = new WebSocketOptions();
websocket_options.AllowedOrigins.Add("*");
app.UseWebSockets(websocket_options);

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseRouting();

app.UseAuthorization();

app.MapControllers();

app.UseTus(httpContext => httpContext.RequestServices.GetRequiredService<DefaultTusConfiguration>());
app.MapGet("/upload/{fileId}", DownloadFileEndpoint.HandleRoute);

app.UseEndpoints(
    endpoints => {
        endpoints.MapHub<Pdf2Epub.API.Hubs.MessageHub>("/hub");
    }
);

SeedData.Seed();

app.Run();


static DefaultTusConfiguration CreateTusConfiguration(IServiceProvider serviceProvider)
{
    var env = (IWebHostEnvironment)serviceProvider.GetRequiredService(typeof(IWebHostEnvironment));

    //文件上传路径
    var tus_root_path = "/root";

    return new DefaultTusConfiguration {
        UrlPath = "/upload",
        //文件存储路径
        Store = new TusDiskStore(tus_root_path),
        Events = new Events {
            OnFileCompleteAsync = async event_context => {
                ITusFile file = await event_context.GetFileAsync();
                Dictionary<string, Metadata> metadata = await file.GetMetadataAsync(event_context.CancellationToken);
                
                // await ((ITusTerminationStore)event_context.Store).DeleteFileAsync(file.Id, event_context.CancellationToken);
            }
        }
    };
}