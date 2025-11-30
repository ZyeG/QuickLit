import { type Settings, type Styles } from "react-chatbotify";
const chatbotSettings: Settings = {
  general: {
    primaryColor: "var(--accent)",
    secondaryColor: "var(--accent-2)",
    fontFamily: "Manrope, 'Segoe UI', sans-serif",
    embedded: false,
    showFooter: false,
  },
  tooltip: {
    mode: "START",
    text: "Ask me anything about academic papers!",
  },
  header: {
    title: "Research Assistant",
    showAvatar: false,
  },
  notification: {
    disabled: true,
    showCount: false,
  },
};

const chatbotStyle: Styles = {
  chatButtonStyle: {
    background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
    color: "#ffffff",
    borderRadius: "14px",
    boxShadow: "0 15px 35px rgba(37, 99, 235, 0.25)",
    border: "1px solid rgba(255, 255, 255, 0.2)",
  },
  chatButtonHoveredStyle: {
    transform: "translateY(-1px)",
    boxShadow: "0 18px 40px rgba(124, 58, 237, 0.28)",
  },
  chatWindowStyle: {
    background: "#ffffff",
    borderRadius: "16px",
    border: "1px solid var(--border)",
    boxShadow: "0 20px 40px rgba(15, 23, 42, 0.12)",
    overflow: "hidden",
  },
  headerStyle: {
    background: "#ffffff",
    color: "var(--text)",
    borderBottom: "1px solid var(--border)",
    fontWeight: 700,
  },
  bodyStyle: {
    backgroundColor: "#f8fafc",
  },
  chatInputContainerStyle: {
    backgroundColor: "#ffffff",
    borderTop: "1px solid var(--border)",
  },
  chatInputAreaStyle: {
    border: "1px solid var(--border)",
    borderRadius: "12px",
    padding: "12px 14px",
    fontSize: "0.95rem",
    backgroundColor: "#ffffff",
    boxShadow: "inset 0 1px 2px rgba(15, 23, 42, 0.04)",
  },
  chatInputAreaFocusedStyle: {
    borderColor: "var(--accent)",
    boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.12)",
  },
  sendButtonStyle: {
    background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    boxShadow: "0 12px 24px rgba(37, 99, 235, 0.25)",
  },
  sendButtonHoveredStyle: {
    transform: "translateY(-1px)",
    boxShadow: "0 16px 30px rgba(124, 58, 237, 0.25)",
  },
  botBubbleStyle: {
    backgroundColor: "#ffffff",
    color: "var(--text)",
    borderRadius: "12px",
    border: "1px solid var(--border)",
    boxShadow: "0 12px 28px rgba(15, 23, 42, 0.08)",
  },
  userBubbleStyle: {
    background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
    color: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0 12px 28px rgba(124, 58, 237, 0.18)",
  },
  tooltipStyle: {
    background: "linear-gradient(135deg, var(--accent), var(--accent-2))",
    color: "#ffffff",
    borderRadius: "10px",
    boxShadow: "0 12px 28px rgba(37, 99, 235, 0.3)",
  },
};

export { chatbotSettings, chatbotStyle };
