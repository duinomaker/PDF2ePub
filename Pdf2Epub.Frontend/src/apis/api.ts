import * as tus from "tus-js-client";

const uri = "https://localhost:49153/upload";

const UploadFile = async (
    file: File,
    location: string,
    OnProcess: (percent: number) => void,
    OnFinish: (url: string | null) => void,
    OnError: () => void
) => {
    let tus_client = new tus.Upload(
        file,
        {
            endpoint: uri,
            retryDelays: [0, 3000, 5000, 10000, 20000],
            metadata: {
                name: file.name,
                contentType: file.type || "application/octet-stream",
                emptyMetaKey: "",
                location: location,
            },
            onError: (error) => {
                console.log("Failed because: " + error);
                OnError();
            },
            onProgress: (bytesUploaded, bytesTotal) => {
                let percent = (bytesUploaded / bytesTotal * 100);
                OnProcess(percent);
            },
            onSuccess: () => {
                console.log("Succeeded. Download %s from %s", (tus_client.file as File).name, tus_client.url);
                OnFinish(tus_client.url);
            }
        }
    );
    tus_client
        .findPreviousUploads()
        .then(
            (previousUploads) => {
                // Found previous uploads so we select the first one.
                if (previousUploads.length) {
                    tus_client.resumeFromPreviousUpload(previousUploads[0]);
                }

                // Start the upload
                tus_client.start();
            }
        );
};

export {UploadFile};