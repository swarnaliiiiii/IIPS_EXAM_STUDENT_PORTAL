import React from "react";
import PropTypes from "prop-types";
import "./Test.css";
import { IoCheckmarkDone } from "react-icons/io5";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkBreaks from "remark-breaks";

const Test = ({ output, loading }) => {
  const stdout = output?.stdout || "";
  const stderr = output?.stderr || "";

  const requiresMarkdown = (text) => {
    // Check for Markdown-like syntax
    return /[*_`[\]]/.test(text);
  };

  const wrapInCodeBlock = (text) => `\`\`\`\n${text}\n\`\`\``;

  return (
    <div className="compiler-test">
      <div className="test-header">
        <IoCheckmarkDone />
        Test Output
      </div>
      <div className="test-output">
        {loading ? (
          <div className="spinner-container">
            <span className="spinner-loader"></span>
          </div>
        ) : (
          <>
            {stdout && (
              <>
                {requiresMarkdown(stdout) ? (
                  <ReactMarkdown
                    className="stdout-output"
                    remarkPlugins={[remarkBreaks]}
                    rehypePlugins={[rehypeSanitize]}
                  >
                    {wrapInCodeBlock(stdout)}
                  </ReactMarkdown>
                ) : (
                  <pre className="stdout-output">{stdout}</pre>
                )}
              </>
            )}
            {stderr && (
              <>
                {requiresMarkdown(stderr) ? (
                  <ReactMarkdown
                    className="stderr-output"
                    remarkPlugins={[remarkBreaks]}
                    rehypePlugins={[rehypeSanitize]}
                  >
                    {wrapInCodeBlock(stderr)}
                  </ReactMarkdown>
                ) : (
                  <pre className="stderr-output">{stderr}</pre>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

Test.propTypes = {
  output: PropTypes.shape({
    stdout: PropTypes.string,
    stderr: PropTypes.string,
  }).isRequired,
  loading: PropTypes.bool.isRequired,
};

export default Test;
