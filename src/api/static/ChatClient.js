// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

class ChatClient {
    constructor(ui) {
        this.ui = ui;
        this.abortController = null; // Will hold the current AbortController instance
    }

    async sendMessage(url, message) {
        if (!message) return false;

        console.log("[ChatClient] Sending message:", message);
        this.ui.appendUserMessage(message);
        document.getElementById("generating-message").style.display = "block";

        const postData = { message: message };

        // Create a new AbortController for this request.
        this.abortController = new AbortController();
        
        try {
            // IMPORTANT: Add credentials: 'include' if server cookies are critical
            // and if your backend is on the same domain or properly configured for cross-site cookies.
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(postData),
                signal: this.abortController.signal,  // attach the signal
                credentials: 'include' // <--- allow cookies to be included
            });

            // Log out the response status in case there’s an error
            console.log("[ChatClient] Response status:", response.status, response.statusText);

            // If server returned e.g. 400 or 500, that’s not an exception, but we can check manually:
            if (!response.ok) {
                console.error("[ChatClient] Response not OK:", response.status, response.statusText);
                return;
            }

            if (!response.body) {
                throw new Error('ReadableStream not supported or response.body is null');
            }

            const agentVariant = response.headers.get('agent-variant');

            console.log("[ChatClient] Starting to handle streaming response...");
            this.handleMessages(response.body, agentVariant);

        } catch (error) {
            document.getElementById("generating-message").style.display = "none";
            if (error.name === 'AbortError') {
                console.log('[ChatClient] Fetch request aborted by user.');
            } else {
                console.error('[ChatClient] Fetch failed:', error);
            }
        } finally {
            // Reset the controller once the request is finished or cancelled
            this.abortController = null;
        }
    }

    handleMessages(stream, agentVariant) {
        let messageDiv = null;
        let accumulatedContent = '';
        let isStreaming = true;
        let buffer = '';
        let annotations = [];

        // Create a reader for the SSE stream
        const reader = stream.getReader();
        const decoder = new TextDecoder();

        const readStream = async () => {
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log("[ChatClient] SSE stream ended by server.");
                    break;
                }

                // Convert the incoming Uint8Array to text
                const textChunk = decoder.decode(value, { stream: true });
                console.log("[ChatClient] Raw chunk from stream:", textChunk);

                buffer += textChunk;
                let boundary = buffer.indexOf('\n');

                // We process line-by-line.
                while (boundary !== -1) {
                    const chunk = buffer.slice(0, boundary).trim();
                    buffer = buffer.slice(boundary + 1);

                    console.log("[ChatClient] SSE line:", chunk); // log each line we extract

                    if (chunk.startsWith('data: ')) {
                        // Attempt to parse JSON
                        const jsonStr = chunk.slice(6);
                        let data;
                        try {
                            data = JSON.parse(jsonStr);
                        } catch (err) {
                            console.error("[ChatClient] Failed to parse JSON:", jsonStr, err);
                            boundary = buffer.indexOf('\n');
                            continue;
                        }

                        console.log("[ChatClient] Parsed SSE event:", data);

                        if (data.error) {
                            if (!messageDiv) {
                                messageDiv = this.ui.createAssistantMessageDiv(agentVariant);
                                console.log("[ChatClient] Created new messageDiv for assistant.");
                            }
                            document.getElementById("generating-message").style.display = "none";
                            this.ui.appendAssistantMessage(
                                messageDiv,
                                data.error.message || "An error occurred.",
                                false
                            );           
                            return;       
                        }

                        // Check the data type to decide how to update the UI
                        if (data.type === "stream_end") {
                            // End of the stream
                            console.log("[ChatClient] Stream end marker received.");
                            messageDiv = null;
                            accumulatedContent = '';
                            break;
                        } else if (data.type === "thread_run") {
                            // Log the run status info
                            console.log("[ChatClient] Run status info:", data.content);
                        } else {
                            // If we have no messageDiv yet, create one
                            if (!messageDiv) {
                                messageDiv = this.ui.createAssistantMessageDiv(agentVariant);
                                console.log("[ChatClient] Created new messageDiv for assistant.");
                            }
                            
                            if (data.type === "completed_message") {
                                this.ui.clearAssistantMessage(messageDiv);
                                accumulatedContent = data.content;
                                annotations = data.annotations;
                                isStreaming = false;
                                console.log("[ChatClient] Received completed message:", accumulatedContent);
                                document.getElementById("generating-message").style.display = "none";
                            } else {
                                accumulatedContent += data.content;
                                console.log("[ChatClient] Received streaming chunk:", data.content);
                            }

                            // Update the UI with the accumulated content
                            this.ui.appendAssistantMessage(
                                messageDiv,
                                accumulatedContent,
                                isStreaming,
                                annotations
                            );
                        }
                    }

                    boundary = buffer.indexOf('\n');
                }
            }
        };

        // Catch errors from the stream reading process
        readStream().catch(error => {
            console.error('[ChatClient] Stream reading failed:', error);
        });
    }

    // Method to abort any in-progress fetch/stream
    closeEventSource() {
        if (this.abortController) {
            this.abortController.abort();
            console.log("[ChatClient] AbortController signaled to cancel ongoing request.");
        }
    }
}

export default ChatClient;
