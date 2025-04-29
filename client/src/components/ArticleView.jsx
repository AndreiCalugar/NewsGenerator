import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getArticleById } from "../services/api";
import ScriptGenerator from "./ScriptGenerator";

const ArticleView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        const response = await getArticleById(id);
        if (response.success) {
          setArticle(response.data);
        } else {
          setError(response.error || "Failed to load article");
        }
      } catch (err) {
        setError("Error connecting to server");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchArticle();
    }
  }, [id]);

  const handleBack = () => {
    navigate("/articles");
  };

  return (
    <div className="article-view">
      <button className="back-button" onClick={handleBack}>
        &larr; Back to Articles
      </button>

      {loading && <div className="loading">Loading article...</div>}

      {error && <div className="error-message">{error}</div>}

      {article && (
        <>
          <div className="article-header">
            <h1>{article.title}</h1>
            <div className="article-meta">
              <span className="source">{article.source}</span>
              {article.published_at && (
                <span className="date">
                  {new Date(article.published_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <div className="article-content">
            <p className="description">{article.description}</p>
            {article.content && (
              <div className="content">{article.content}</div>
            )}
          </div>

          <div key={`script-container-${id}`} className="script-container">
            <ScriptGenerator articleId={id} articleTitle={article.title} />
          </div>
        </>
      )}
    </div>
  );
};

export default ArticleView;
