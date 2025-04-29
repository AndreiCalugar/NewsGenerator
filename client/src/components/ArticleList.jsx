import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchNewsArticles } from "../services/api";

const ArticleList = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadArticles = async () => {
      try {
        setLoading(true);
        const response = await fetchNewsArticles();
        if (response.success) {
          setArticles(response.data.articles);
        } else {
          setError(response.error || "Failed to load articles");
        }
      } catch (err) {
        setError("Error connecting to server");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadArticles();
  }, []);

  return (
    <div className="article-list">
      <h1>Latest News Articles</h1>
      <p>Select an article to generate a video</p>

      {loading && <div className="loading">Loading articles...</div>}

      {error && <div className="error-message">{error}</div>}

      {!loading && articles.length === 0 && !error && (
        <div className="no-articles">No articles found.</div>
      )}

      <div className="articles-grid">
        {articles.map((article) => (
          <Link
            to={`/articles/${article.id}`}
            key={article.id}
            className="article-card"
          >
            <h3>{article.title}</h3>
            <div className="article-source">{article.source}</div>
            <p>{article.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default ArticleList;
