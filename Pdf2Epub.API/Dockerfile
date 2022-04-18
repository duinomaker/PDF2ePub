#See https://aka.ms/containerfastmode to understand how Visual Studio uses this Dockerfile to build your images for faster debugging.

FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /app
EXPOSE 80
EXPOSE 443

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["Pdf2Epub.API/Pdf2Epub.API.csproj", "Pdf2Epub.API/"]
RUN dotnet restore "Pdf2Epub.API/Pdf2Epub.API.csproj"
COPY . .
WORKDIR "/src/Pdf2Epub.API"
RUN dotnet build "Pdf2Epub.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Pdf2Epub.API.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Pdf2Epub.API.dll"]