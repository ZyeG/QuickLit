import React from "react";
import "./PaperListItem.css";

export interface Paper {
  title: string;
  pdf_link: string;
}

interface Props {
  paper: Paper;
  summaryData: any;
  isHovered: boolean;
  isClicked: boolean;
  isLoadingSummary: boolean;
  onHoverEnter: () => void;
  onHoverLeave: () => void;
  onButtonClick: () => void;
}

export default function PaperListItem({
  paper,
  summaryData,
  isHovered,
  isClicked,
  isLoadingSummary,
  onHoverEnter,
  onHoverLeave,
  onButtonClick,
}: Props) {
  return (
    <li className="paper-item">
      <div>
        <a
          href={paper.pdf_link}
          target="_blank"
          rel="noopener noreferrer"
          className="paper-link"
        >
          {paper.title}
        </a>
      </div>

      {/* Summary button with hover popup */}
      <div
        className="paper-actions"
        onMouseEnter={onHoverEnter}
        onMouseLeave={onHoverLeave}
      >
        <button
          onClick={onButtonClick}
          disabled={isLoadingSummary}
          className={`paper-btn ${isClicked ? "clicked" : ""} ${
            isLoadingSummary ? "loading" : ""
          }`}
        >
          {isLoadingSummary
            ? "Summarizing..."
            : isClicked
            ? "Display"
            : "Get Summary"}
        </button>

        {/* Hover popup for completed summaries */}
        {isHovered && summaryData && !isLoadingSummary && (
          <div
            className={`paper-popup ${
              summaryData.type === "abstract" ? "abstract" : ""
            }`}
          >
            <strong>
              {summaryData.type === "abstract" ? "Abstract" : "Summary"}
            </strong>
            <div style={{ marginTop: "0.5rem" }}>{summaryData.summary}</div>
            {summaryData.warning && (
              <div className="warning">⚠️ {summaryData.warning}</div>
            )}
            {summaryData.cached && <div className="cached">(Cached)</div>}
          </div>
        )}
      </div>
    </li>
  );
}
