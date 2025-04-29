import React from "react";
import { Link, useLocation } from "react-router-dom";

const Navbar = () => {
  const location = useLocation();

  // Helper to determine if a link is active
  const isActive = (path) => {
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">AutoVid</Link>
      </div>
      <ul className="navbar-menu">
        <li className={isActive("/articles") ? "active" : ""}>
          <Link to="/articles">News Articles</Link>
        </li>
        <li className={isActive("/custom") ? "active" : ""}>
          <Link to="/custom">Custom Text</Link>
        </li>
        <li className={isActive("/videos") ? "active" : ""}>
          <Link to="/videos">My Videos</Link>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
