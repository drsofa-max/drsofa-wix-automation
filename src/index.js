/**
 * Cloudflare Worker - Wix API Proxy
 * Routes requests to Wix API with proper authentication
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Route all Wix blog API requests through this worker
    if (path.startsWith('/wix/')) {
      return handleWixBlogRequest(request, path);
    }

    // Default 404 for unmatched routes
    return new Response(JSON.stringify({ error: 'Route not found', path }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' }
    });
  }
};

async function handleWixBlogRequest(request, path) {
  // Extract headers needed for Wix API
  const wixApiKey = request.headers.get('Authorization');
  const wixSiteId = request.headers.get('wix-site-id');
  const wixAccountId = request.headers.get('wix-account-id');
  const contentType = request.headers.get('Content-Type') || 'application/json';

  if (!wixApiKey || !wixAccountId) {
    return new Response(
      JSON.stringify({ error: 'Missing required Wix headers (Authorization, wix-account-id)' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  // Build the actual Wix API URL
  // Path format: /wix/blog/v3/posts or /wix/blog/v3/posts/{id}
  const wixPath = path.replace('/wix', '');
  const wixUrl = `https://www.wixapis.com${wixPath}`;

  // Prepare headers for Wix API
  const wixHeaders = new Headers({
    'Authorization': wixApiKey,
    'wix-account-id': wixAccountId,
    'Content-Type': contentType
  });

  if (wixSiteId) {
    wixHeaders.set('wix-site-id', wixSiteId);
  }

  // Copy body for POST/PUT requests
  let body = null;
  if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
    body = await request.text();
  }

  try {
    // Make the request to Wix API
    const wixResponse = await fetch(wixUrl, {
      method: request.method,
      headers: wixHeaders,
      body: body,
      timeout: 30000
    });

    // Return the Wix API response
    const responseBody = await wixResponse.text();
    return new Response(responseBody, {
      status: wixResponse.status,
      headers: {
        'Content-Type': wixResponse.headers.get('Content-Type') || 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: `Proxy error: ${error.message}`,
        path: wixUrl,
        method: request.method
      }),
      { status: 502, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
