using Microsoft.AspNetCore.SignalR;

namespace Pdf2Epub.API.Hubs
{
    public class MessageHub : Hub
    {
        public delegate void MessageHandler(string message);
        MessageHandler? message_handler = null;

        public async Task DistributeMessage(string message)
        {
            await Clients.All.SendAsync("ReceiveMessage", message);
        }

        public void HandleMessage(string message)
        {
            message_handler?.Invoke(message);
        }
    }
}
