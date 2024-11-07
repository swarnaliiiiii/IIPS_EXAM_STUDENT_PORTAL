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
              <ReactMarkdown
                className="stdout-output"
                remarkPlugins={[remarkBreaks]}
                rehypePlugins={[rehypeSanitize]}
              >
                {stdout}
              </ReactMarkdown>
            )}
            {stderr && (
              <ReactMarkdown
                className="stderr-output"
                remarkPlugins={[remarkBreaks]}
                rehypePlugins={[rehypeSanitize]}
              >
                {stderr}
              </ReactMarkdown>
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
  loading: PropTypes.bool.isRequired, // Add loading prop type
};

export default Test;
