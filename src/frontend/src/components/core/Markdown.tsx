import type {
  AnchorHTMLAttributes,
  ClassAttributes,
  HTMLAttributes,
  PropsWithChildren,
} from "react";
import type { ExtraProps } from "react-markdown";

import { Text } from "@fluentui/react-components";
import { CopyRegular } from "@fluentui/react-icons";
import copy from "copy-to-clipboard";
import { Fragment, isValidElement, memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import SyntaxHighlighter from "react-syntax-highlighter";
import { docco } from "react-syntax-highlighter/dist/esm/styles/hljs";
import RehypeKatex from "rehype-katex";
import RehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";
import RemarkBreaks from "remark-breaks";
import RemarkGfm from "remark-gfm";
import RemarkMath from "remark-math";
import remarkParse from "remark-parse";
import supersub from "remark-supersub";

import { Button } from "@fluentui/react-components";

import { ThinkBlock } from "./ThinkBlock";

import styles from "./Markdown.module.css";

interface ICitation extends React.JSX.Element {
  props: {
    "data-replace"?: string;
    [key: string]: unknown;
  };
}

interface IMarkdownProps {
  citations?: ICitation[] | undefined;
  content: string;
  className?: string;
  customDisallowedElements?: string[];
}

interface IRehypeNode {
  type: string;
  tagName: string;
  properties?: { ref?: unknown; [key: string]: unknown };
  children?: IRehypeNode[];
  value?: string;
}

function Hyperlink({
  node,
  children,
  ...linkProps
}: ClassAttributes<HTMLAnchorElement> &
  AnchorHTMLAttributes<HTMLAnchorElement> &
  ExtraProps) {
  return (
    <a
      href={node?.properties.href?.toString() ?? ""}
      target="_blank"
      rel="noopener noreferrer"
      className={styles.link}
      {...linkProps}
    >
      {children}
    </a>
  );
}

interface ICodeBlockProps
  extends ClassAttributes<HTMLElement>,
    HTMLAttributes<HTMLElement>,
    ExtraProps {
  inline?: boolean;
}

// Preprocesses LaTeX notation to standard math notation for the markdown parser
const preprocessLaTeX = (content: string): string => {
  if (typeof content !== "string") {
    return content;
  }

  // Convert \[ ... \] to $$ ... $$
  let result = content.replaceAll(
    /\\\[(.*?)\\\]/g,
    (_: string, equation: string) => `$$${equation}$$`
  );

  // Convert \( ... \) to $ ... $
  result = result.replaceAll(
    /\\\((.*?)\\\)/g,
    (_: string, equation: string) => `$${equation}$$`
  );

  // Handle $ notation
  result = result.replaceAll(
    /(^|[^\\])\$(.+?)\$/g,
    (_: string, prefix: string, equation: string) => `${prefix}$${equation}$`
  );

  return result;
};

// Preprocesses <think> tags to convert them to <details> with special attributes
const preprocessThinkTag = (content: string): string => {
  const thinkTagRegex = /<think>\n([\s\S]*?)\n<\/think>/g;

  // Replace <think> tags with <details> only if there's content inside
  return content.replaceAll(
    thinkTagRegex,
    (_match: string, innerContent: string) => {
      // If the inner content is empty or only whitespace, return empty string
      if (!innerContent.trim()) {
        return "";
      }
      // Otherwise, replace with details tag
      return `<details data-think=true>\n${innerContent}\n[ENDTHINKFLAG]</details>`;
    }
  );
};

const CodeBlock = memo<ICodeBlockProps>(
  ({ inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className ?? "");

    if (inline || !match) {
      return (
        <code {...props} className={styles.inlineCode}>
          {children}
        </code>
      );
    }

    const language = match[1];
    const content = String(children)
      .replace(/\n$/, "")
      .replaceAll("&nbsp;", "");

    return (
      <div className={styles.codeBlock}>
        <div className={styles.codeHeader}>
          <Text weight="semibold">{language}</Text>
          <div className={styles.alignRight}>
            <Button
              appearance="subtle"
              icon={<CopyRegular />}
              onClick={() => {
                copy(content);
              }}
            >
              Copy
            </Button>
          </div>
        </div>
        <SyntaxHighlighter
          PreTag="div"
          customStyle={{
            margin: 0,
            borderBottomLeftRadius: "6px",
            borderBottomRightRadius: "6px",
          }}
          language={language}
          showLineNumbers={true}
          style={docco}
        >
          {content}
        </SyntaxHighlighter>
      </div>
    );
  }
);

CodeBlock.displayName = "CodeBlock";

function Paragraph({
  children,
  className,
}: PropsWithChildren<{
  className?: string;
}>) {
  return <span className={className}>{children} </span>;
}

export function Markdown({
  citations,
  content,
  className,
  customDisallowedElements,
}: IMarkdownProps): React.ReactElement {
  const segments = useMemo(() => {
    if (!citations || citations.length === 0) {
      return [
        {
          type: "text" as const,
          content: preprocessThinkTag(preprocessLaTeX(content)),
        },
      ];
    }

    const parts: {
      type: "text" | "citation";
      content: string | React.JSX.Element;
    }[] = [];
    let lastIndex = 0;

    for (const citation of citations) {
      const replaceText = String(citation.props["data-replace"] ?? "");
      const index = content.indexOf(replaceText, lastIndex);

      if (index !== -1) {
        if (index > lastIndex) {
          const textContent = content.slice(lastIndex, index);
          parts.push({
            type: "text",
            content: preprocessThinkTag(preprocessLaTeX(textContent)),
          });
        }

        parts.push({
          type: "citation",
          content: citation,
        });

        lastIndex = index + replaceText.length;
      }
    }

    if (lastIndex < content.length) {
      const textContent = content.slice(lastIndex);
      parts.push({
        type: "text",
        content: preprocessThinkTag(preprocessLaTeX(textContent)),
      });
    }

    return parts;
  }, [content, citations]);

  return (
    <div className={`${styles.markdown} ${className ?? ""}`}>
      {segments.map((segment, idx) => (
        <Fragment
          key={
            segment.type === "citation" && isValidElement(segment.content)
              ? segment.content.key ?? idx
              : idx
          }
        >
          {segment.type === "text" ? (
            <ReactMarkdown
              components={{
                code: CodeBlock,
                a: Hyperlink,
                details: ThinkBlock,
                p: Paragraph,
              }}
              disallowedElements={[
                "iframe",
                "head",
                "html",
                "meta",
                "link",
                "style",
                "body",
                ...(customDisallowedElements ?? []),
              ]}
              rehypePlugins={[
                RehypeKatex,
                RehypeRaw,
                rehypeStringify,
                [
                  rehypeSanitize,
                  {
                    ...defaultSchema,
                    tagNames: [...(defaultSchema.tagNames ?? []), "sub", "sup"],
                    attributes: {
                      ...defaultSchema.attributes,
                      code: [["className", /^language-./]],
                    },
                  },
                ],
                // Remove ref properties and validate tag names
                () => (tree: { children: IRehypeNode[] }) => {
                  const iterate = (node: IRehypeNode) => {
                    if (
                      node.type === "element" &&
                      node.properties !== undefined &&
                      "ref" in node.properties
                    ) {
                      delete node.properties.ref;
                    }

                    if (
                      node.type === "element" &&
                      !/^[a-z][a-z0-9]*$/i.test(node.tagName)
                    ) {
                      node.type = "text";
                      node.value = `<${node.tagName}`;
                    }

                    if (node.children) {
                      for (const child of node.children) {
                        iterate(child);
                      }
                    }
                  };

                  for (const child of tree.children) {
                    iterate(child);
                  }
                },
              ]}
              remarkPlugins={[
                RemarkGfm,
                [RemarkMath, { singleDollarTextMath: false }],
                RemarkBreaks,
                supersub,
                remarkParse,
              ]}
            >
              {segment.content as string}
            </ReactMarkdown>
          ) : (
            segment.content
          )}
        </Fragment>
      ))}
    </div>
  );
}
