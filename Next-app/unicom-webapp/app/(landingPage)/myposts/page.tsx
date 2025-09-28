"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../../utils/AuthProvider";
import infra_config from '../../../public/infra_config.json';

// Simple date formatting functions
const formatDateUTC = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString();
};

const formatDateTimeUTC = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

// Default images for categories
const DEFAULT_IMAGES: Record<string, string> = {
  CARPOOL: "/carpool.png",
  ROOMMATE: "/Roommate.png",
  SELL: "/sell.png",
};

interface Post {
  _id: string;
  title: string;
  price?: number;
  location?: string;
  images?: Array<{
    image_id: string;
    filename: string;
    urls: {
      thumbnail: string;
      medium: string;
      large: string;
    };
  }>;
  category: string;
  owner: string;
  description?: string;
  status: string;
  // Roommate-specific fields
  community?: string;
  rent?: number;
  start_date?: string;
  gender_preference?: string;
  preferences?: string[];
  // Carpool-specific fields
  from_location?: string;
  to_location?: string;
  departure_time?: string;
  seats_available?: number;
  // Sell-specific fields
  item?: string;
  sub_category?: string;
}

const API_BASE_URL = infra_config.api_url;

export default function MyPostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(9);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState("");
  const [sortOrder, setSortOrder] = useState("desc");

  const { getValidToken } = useAuth();

  // Helper function to get the image URL
  const getPostImage = (post: Post): string => {
    if (post.images && post.images.length > 0) {
      const urls = post.images[0].urls || {};
      let imageUrl = '';
      
      // Prefer medium > large > thumbnail
      if (urls.medium) imageUrl = urls.medium;
      else if (urls.large) imageUrl = urls.large;
      else if (urls.thumbnail) imageUrl = urls.thumbnail;
      
      // If we have an imageUrl, construct full URL with API_BASE_URL
      if (imageUrl) {
        // If it's already an absolute URL, return as-is
        if (imageUrl.startsWith("http")) return imageUrl;
        
        // Your API serves images at the exact path stored in the database
        const fullUrl = `${API_BASE_URL}${imageUrl}`;
        console.log(`Constructed image URL: ${fullUrl}`);
        return fullUrl;
      }
    }
    
    // Fallback: default category images from /public
    const fallback = DEFAULT_IMAGES[post.category] || "/default.png";
    console.log(`Using fallback image: ${fallback}`);
    return fallback;
  };

  // Helper function for image error handling
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>, post: Post) => {
    const target = e.target as HTMLImageElement;
    const fallbackSrc = DEFAULT_IMAGES[post.category] || '/default.png';
    
    // Only change src if it's not already the fallback to prevent infinite loops
    if (target.src !== window.location.origin + fallbackSrc) {
      console.log(`Image failed to load: ${target.src}, falling back to: ${fallbackSrc}`);
      target.src = fallbackSrc;
    }
  };

  const fetchMyPosts = async () => {
    try {
      setLoading(true);
      const token = await getValidToken();
      if (!token) {
        console.error("No token available");
        return;
      }

      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(searchQuery && { search: searchQuery }),
        ...(category && { category }),
        sort: sortOrder
      });

      const response = await fetch(`${API_BASE_URL}/api/myposts?${params}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.error("Failed to fetch posts", response.status);
        return;
      }

      const data = await response.json();
      setPosts(data.posts || []);
      setTotal(data.total || 0);

    } catch (error) {
      console.error("Error fetching posts:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      const token = await getValidToken();
      if (!token) {
        console.error("No token available");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        console.error("Failed to delete post", response.status);
        return;
      }

      setPosts(posts.filter((post) => post._id !== postId));
      setTotal((prev) => prev - 1);
      
      // Close modal if deleted post is currently selected
      if (selectedPost && selectedPost._id === postId) {
        setSelectedPost(null);
      }
    } catch (error) {
      console.error("Error deleting post:", error);
    }
  };

  const handleUpdatePostStatus = async (postId: string, newStatus: string) => {
    try {
      const token = await getValidToken();
      if (!token) {
        console.error("No valid token available");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/posts/${postId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        console.error("Failed to update post status", response.status);
        return;
      }

      setPosts(
        posts.map((post) =>
          post._id === postId ? { ...post, status: newStatus } : post
        )
      );

      if (selectedPost && selectedPost._id === postId) {
        setSelectedPost({ ...selectedPost, status: newStatus });
      }
    } catch (error) {
      console.error("Error updating post status:", error);
    }
  };

  useEffect(() => {
    fetchMyPosts();
  }, [page, limit, searchQuery, category, sortOrder]);

  const handleNext = () => {
    if (page * limit < total) {
      setPage((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (page > 1) {
      setPage((prev) => prev - 1);
    }
  };

  const closeModal = () => setSelectedPost(null);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4 relative">
      <section className="max-w-6xl mx-auto p-4">
        <h2 className="text-2xl font-semibold mb-4">My Posts</h2>

        {/* Search */}
        <div className="flex items-center mb-6">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search my posts..."
            className="border p-2 rounded-l-md w-full max-w-md"
          />
          <button
            onClick={() => {
              setPage(1);
              setSearchQuery(searchTerm);
            }}
            className="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600"
          >
            Search
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="border p-2 rounded-md"
          >
            <option value="">All Categories</option>
            <option value="SELL">Sell</option>
            <option value="ROOMMATE">Roommate</option>
            <option value="CARPOOL">Carpool</option>
          </select>

          <select
            value={sortOrder}
            onChange={(e) => {
              setSortOrder(e.target.value);
              setPage(1);
            }}
            className="border p-2 rounded-md"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>

        {/* Posts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {posts.map((post) => {
            const imageUrl = getPostImage(post);

            return (
              <div
                key={post._id}
                className={`border rounded-md overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition relative ${
                  post.status === "FAILED" ? "bg-red-100" : "bg-white"
                }`}
              >
                <div
                  className="h-48 w-full bg-gray-200"
                  onClick={() => setSelectedPost(post)}
                >
                  <img
                    src={imageUrl}
                    alt={post.title}
                    className="object-cover h-full w-full"
                    onError={(e) => handleImageError(e, post)}
                  />
                </div>
                <div className="p-4">
                  {/* Title and Category */}
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-bold">{post.title}</h3>
                    <span className="text-xs uppercase bg-gray-200 text-gray-700 px-2 py-1 rounded">
                      {post.category}
                    </span>
                  </div>

                  {/* Status */}
                  <p className="text-sm text-gray-500 mb-2">Status: {post.status}</p>

                  {/* Category-specific details */}
                  {post.category === "SELL" && (
                    <div className="text-gray-700 space-y-1">
                      {post.item && <p>Item: {post.item}</p>}
                      {post.price !== undefined && (
                        <p className="text-green-700 font-semibold text-lg">
                          ${post.price}
                        </p>
                      )}
                      {post.sub_category && (
                        <p>Subcategory: {post.sub_category}</p>
                      )}
                    </div>
                  )}
                  {post.category === "ROOMMATE" && (
                    <div className="text-gray-700 space-y-1">
                      {post.community && (
                        <p>Community: {post.community}</p>
                      )}
                      {post.rent !== undefined && (
                        <p className="text-green-700 font-semibold text-lg">
                          Rent: ${post.rent}
                        </p>
                      )}
                      {post.start_date && (
                        <p className="text-gray-700">
                          Start Date: {formatDateUTC(post.start_date)}
                        </p>
                      )}
                      {post.gender_preference && (
                        <p>
                          Gender Preference: {post.gender_preference}
                        </p>
                      )}
                      {/* Preferences Tags */}
                      {post.preferences && post.preferences.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {post.preferences.map((pref, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded"
                            >
                              {pref}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {post.category === "CARPOOL" && (
                    <div className="text-gray-700 space-y-1">
                      {post.from_location && (
                        <p>From: {post.from_location}</p>
                      )}
                      {post.to_location && (
                        <p>To: {post.to_location}</p>
                      )}
                      {post.departure_time && (
                        <p className="text-gray-700">
                          Departure: {formatDateTimeUTC(post.departure_time)}
                        </p>
                      )}
                      {post.seats_available !== undefined && (
                        <p>
                          Seats Available: {post.seats_available}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Posted By */}
                  <div className="mt-3">
                    <p className="text-sm text-gray-500">
                      Posted by: {post.owner}
                    </p>
                  </div>

                  {/* Post Management Buttons */}
                  <div className="mt-4 flex gap-2">
                    {post.status !== "CLOSED" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUpdatePostStatus(post._id, "CLOSED");
                        }}
                        className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                      >
                        Close
                      </button>
                    )}
                    {post.status === "CLOSED" && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUpdatePostStatus(post._id, "PUBLISHED");
                        }}
                        className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                      >
                        Publish
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this post?')) {
                          handleDeletePost(post._id);
                        }
                      }}
                      className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Pagination Controls */}
        {total > 0 && (
          <div className="flex justify-between items-center mt-8">
            <button
              onClick={handlePrev}
              disabled={page === 1}
              className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <p className="text-gray-700">
              Page {page} of {Math.ceil(total / limit)} ({total} posts)
            </p>
            <button
              onClick={handleNext}
              disabled={page * limit >= total}
              className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && posts.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No posts found</p>
            <p className="text-gray-400">Try adjusting your search or create a new post</p>
          </div>
        )}
      </section>

      {/* Modal Popup */}
      <AnimatePresence>
        {selectedPost && (
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed top-0 right-0 w-full md:w-1/2 h-full bg-white shadow-2xl z-50 overflow-auto"
          >
            <div className="p-6">
              <button
                onClick={closeModal}
                className="mb-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
              >
                Close
              </button>

              <h2 className="text-2xl font-bold mb-2">{selectedPost.title}</h2>
              <p className="text-gray-600 mb-4">{selectedPost.category}</p>
              <p className="text-gray-600 mb-4">Status: {selectedPost.status}</p>

              {/* Images */}
              <div className="flex flex-wrap justify-center gap-4 mt-4">
                {selectedPost.images && selectedPost.images.length > 0 ? (
                  selectedPost.images.map((img, idx) => {
                    const imageUrl = img.urls.large || img.urls.medium || img.urls.thumbnail;
                    const fullImageUrl = imageUrl.startsWith('http') 
                      ? imageUrl 
                      : `${API_BASE_URL}${imageUrl}`;
                    
                    return (
                      <img
                        key={idx}
                        src={fullImageUrl}
                        alt={`Image ${idx + 1} for ${selectedPost.title}`}
                        className="w-full max-w-xs h-64 object-cover rounded-md shadow-md"
                        onError={(e) => handleImageError(e, selectedPost)}
                      />
                    );
                  })
                ) : (
                  <img
                    src={getPostImage(selectedPost)}
                    alt={selectedPost.title}
                    className="w-full max-w-xs h-64 object-cover rounded-md shadow-md"
                    onError={(e) => handleImageError(e, selectedPost)}
                  />
                )}
              </div>

              {/* Category-specific details */}
              {selectedPost.category === "SELL" && (
                <div className="mt-4 text-gray-700 space-y-2">
                  {selectedPost.item && <p><strong>Item:</strong> {selectedPost.item}</p>}
                  {selectedPost.price !== undefined && (
                    <p className="text-green-700 font-semibold text-lg">
                      <strong>Price:</strong> ${selectedPost.price}
                    </p>
                  )}
                  {selectedPost.sub_category && (
                    <p><strong>Subcategory:</strong> {selectedPost.sub_category}</p>
                  )}
                </div>
              )}

              {selectedPost.category === "ROOMMATE" && (
                <div className="mt-4 text-gray-700 space-y-2">
                  {selectedPost.community && (
                    <p><strong>Community:</strong> {selectedPost.community}</p>
                  )}
                  {selectedPost.rent !== undefined && (
                    <p className="text-green-700 font-semibold text-lg">
                      <strong>Rent:</strong> ${selectedPost.rent}
                    </p>
                  )}
                  {selectedPost.start_date && (
                    <p>
                      <strong>Start Date:</strong> {formatDateUTC(selectedPost.start_date)}
                    </p>
                  )}
                  {selectedPost.gender_preference && (
                    <p>
                      <strong>Gender Preference:</strong> {selectedPost.gender_preference}
                    </p>
                  )}
                  {selectedPost.preferences && selectedPost.preferences.length > 0 && (
                    <div>
                      <p className="font-semibold mb-2">Preferences:</p>
                      <div className="flex flex-wrap gap-2">
                        {selectedPost.preferences.map((pref, idx) => (
                          <span
                            key={idx}
                            className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded"
                          >
                            {pref}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectedPost.category === "CARPOOL" && (
                <div className="mt-4 text-gray-700 space-y-2">
                  {selectedPost.from_location && (
                    <p><strong>From:</strong> {selectedPost.from_location}</p>
                  )}
                  {selectedPost.to_location && (
                    <p><strong>To:</strong> {selectedPost.to_location}</p>
                  )}
                  {selectedPost.departure_time && (
                    <p>
                      <strong>Departure:</strong> {formatDateTimeUTC(selectedPost.departure_time)}
                    </p>
                  )}
                  {selectedPost.seats_available !== undefined && (
                    <p>
                      <strong>Seats Available:</strong> {selectedPost.seats_available}
                    </p>
                  )}
                </div>
              )}

              <p className="text-gray-500 mt-4">
                <strong>Posted by:</strong> {selectedPost.owner}
              </p>

              {selectedPost.description && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold mb-2">Description</h3>
                  <p className="text-gray-700">{selectedPost.description}</p>
                </div>
              )}

              {/* Post Management Buttons in Modal */}
              <div className="mt-6 flex gap-2">
                {selectedPost.status !== "CLOSED" && (
                  <button
                    onClick={() => handleUpdatePostStatus(selectedPost._id, "CLOSED")}
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    Close Post
                  </button>
                )}
                {selectedPost.status === "CLOSED" && (
                  <button
                    onClick={() => handleUpdatePostStatus(selectedPost._id, "PUBLISHED")}
                    className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    Publish Post
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this post?')) {
                      handleDeletePost(selectedPost._id);
                    }
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                >
                  Delete Post
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}