import ChatBot from "react-chatbotify";
import { type Flow, type Params } from "react-chatbotify";
import { chatbotSettings, chatbotStyle } from "./chatbotSetting";
type MyProps = {
  collection_name: string;
  disabled?: boolean;
};
const REACT_APP_API_URL = "http://localhost:3001/api/chat/stream";
function MyChatBot({ collection_name, disabled = false }: MyProps) {
  let error = false;
  let url = REACT_APP_API_URL || " ";
  const chat_stream = async (params: Params) => {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query_text: params.userInput,
          collection_name: collection_name,
        }),
        mode: "cors",
      });

      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);

      // Pipe the byte stream through a TextDecoderStream → gives you a stream of strings
      if (!res.body) {
        throw new Error("Empty response body");
      }
      const textStream = res.body
        .pipeThrough(new TextDecoderStream())
        .getReader();

      // Stream generator to read the text stream
      async function* textGenerator() {
        try {
          while (true) {
            const { value, done } = await textStream.read();
            if (done) break;
            yield value;
          }
        } finally {
          textStream.releaseLock();
        }
      }

      let text = "";

      for await (const chunkText of textGenerator()) {
        text += chunkText;
        await params.streamMessage(text, "bot");
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      await params.streamMessage(text, "bot");
      await params.endStreamMessage("bot");
    } catch (e) {
      error = true;
      console.error("Error:", e);
    }
  };
  const flow: Flow = {
    start: {
      message:
        "Hello! How can I assist you with your research today? Ask me anything about academic papers that you have researched!",
      path: "loop",
    },
    loop: {
      message: async (params: Params) => {
        await chat_stream(params);
      },
      path: () => {
        if (error) {
          return "error_end";
        } else {
          return "loop";
        }
      },
      // If an error occurs, chat will be disabled
      chatDisabled: async () => {
        return error || disabled;
      },
    },
    error_end: {
      message: "sorry, something went wrong.",
      chatDisabled: true,
    },
  };
  return (
    <ChatBot flow={flow} settings={chatbotSettings} styles={chatbotStyle} />
  );
}

export default MyChatBot;
