#See https://aka.ms/containerfastmode to understand how Visual Studio uses this Dockerfile to build your images for faster debugging.

FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /py_pdfepub
COPY ["Pdf2Epub.Worker/py_pdfepub", "."]
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && pip install matplotlib nltk numpy PyMuPDF \
    && mv /py_pdfepub/nltk_data /usr/share
WORKDIR /app
EXPOSE 80
EXPOSE 443
    

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["Pdf2Epub.Worker/Pdf2Epub.Worker.csproj", "Pdf2Epub.Worker/"]
RUN dotnet restore "Pdf2Epub.Worker/Pdf2Epub.Worker.csproj"
COPY . .
WORKDIR "/src/Pdf2Epub.Worker"
RUN dotnet build "Pdf2Epub.Worker.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Pdf2Epub.Worker.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Pdf2Epub.Worker.dll"]