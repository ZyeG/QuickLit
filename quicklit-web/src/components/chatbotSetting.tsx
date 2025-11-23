import { type Settings, type Styles } from "react-chatbotify";
const chatbotSettings: Settings = {
  general: {
    embedded: false,
    showFooter: false,
  },
  tooltip: {
    mode: "START",
    text: "Ask me anything about academic papers!",
  },
  header: {
    title: "Reasearch Assistant",
    showAvatar: false,
  },
  notification: {
    disabled: true,
    showCount: false,
  },
};

const chatbotStyle: Styles = {
  headerStyle: {
    background: "#ffffff",
    color: "#000000",
  },
  sendButtonStyle: {
    backgroundColor: "#428EC5",
    color: "white",
  },
  sendButtonHoveredStyle: {
    backgroundColor: "#90BFF9",
    color: "white",
  },
  botBubbleStyle: {
    backgroundColor: "#49494B",
    color: "#ffffff",
    borderRadius: "10px",
    boxShadow: "1px 3px 5px rgba(0, 0, 0, 0.5)",
  },
  userBubbleStyle: {
    backgroundColor: "#428EC5",
    color: "#ffffff",
    borderRadius: "10px",
    boxShadow: "1px 3px 5px rgba(0, 0, 0, 0.5)",
  },
  tooltipStyle: {
    backgroundColor: "#428EC5",
    color: "#ffffff",
    borderRadius: "5px",
    boxShadow: "1px 3px 5px rgba(0, 0, 0, 0.5)",
  },
};

export { chatbotSettings, chatbotStyle };
