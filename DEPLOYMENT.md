# Deployment Guide - CodePilot

This guide explains how to deploy CodePilot to Render (recommended) or other platforms.

## Option 1: Deploy to Render (Recommended)

Render offers a free tier and easy deployment from GitHub.

### Step 1: Prerequisites
- GitHub account with CodePilot repository
- Render account (sign up at https://render.com)
- OpenAI API key
- E2B API key

### Step 2: Deploy from GitHub

1. **Fork/Push to GitHub**: Ensure your code is pushed to GitHub

2. **Create New Web Service on Render**:
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `codepilot` repository

3. **Configure Service**:
   - **Name**: `codepilot` (or your preferred name)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `chainlit run chainlit_app.py --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   Go to "Environment" tab and add:
   ```
   OPENAI_API_KEY=your_openai_key_here
   E2B_API_KEY=your_e2b_key_here
   CHAINLIT_PASSWORD=your_secure_password_here
   PYTHON_VERSION=3.11.0
   ```

5. **Deploy**: Click "Create Web Service"

The deployment will start automatically. It takes 3-5 minutes for the first deploy.

### Step 3: Access Your App

Once deployed, access your app at:
```
https://your-app-name.onrender.com
```

Default login credentials:
- Username: Any username
- Password: Value you set in `CHAINLIT_PASSWORD`

## Option 2: Deploy to Railway

1. Install Railway CLI:
   ```bash
   npm install -g railway
   ```

2. Login and initialize:
   ```bash
   railway login
   railway init
   ```

3. Add environment variables:
   ```bash
   railway variables set OPENAI_API_KEY=your_key
   railway variables set E2B_API_KEY=your_key
   railway variables set CHAINLIT_PASSWORD=your_password
   ```

4. Deploy:
   ```bash
   railway up
   ```

## Option 3: Deploy to Fly.io

1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login and launch:
   ```bash
   fly auth login
   fly launch
   ```

3. Set secrets:
   ```bash
   fly secrets set OPENAI_API_KEY=your_key
   fly secrets set E2B_API_KEY=your_key
   fly secrets set CHAINLIT_PASSWORD=your_password
   ```

4. Deploy:
   ```bash
   fly deploy
   ```

## Environment Variables

Required environment variables for deployment:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `E2B_API_KEY` | Your E2B API key for sandbox execution | Yes |
| `CHAINLIT_PASSWORD` | Password to access the UI | Yes |
| `PYTHON_VERSION` | Python version (3.11+) | No (defaults to latest) |

## Cost Considerations

### Free Tier Limits

**Render Free Tier**:
- 750 hours/month (enough for hobby projects)
- Sleeps after 15 minutes of inactivity
- Wakes up on request (takes ~30 seconds)

**OpenAI API** (~$0.02 per task with GPT-3.5-turbo):
- $5 free credit for new accounts
- Pay-as-you-go after that

**E2B Sandbox**:
- Free tier available
- Check https://e2b.dev/pricing for details

### Reducing Costs

1. **Use GPT-3.5-turbo** (default): 20x cheaper than GPT-4
2. **Lower max_iterations**: Set to 3 (current default)
3. **Monitor usage**: Check the cost tracker in the UI
4. **Set API spending limits**: Configure in OpenAI dashboard

## Troubleshooting

### App won't start
- Check environment variables are set correctly
- Verify Python version is 3.11+
- Check build logs for errors

### Authentication not working
- Ensure `CHAINLIT_PASSWORD` is set
- Try clearing browser cookies
- Check `.chainlit/config.toml` exists

### High API costs
- Check max_iterations setting (should be 3 or less)
- Verify using GPT-3.5-turbo (not GPT-4)
- Monitor costs in real-time via the UI

### Sandbox errors
- Verify E2B_API_KEY is valid
- Check E2B quota at https://e2b.dev/dashboard
- Ensure network access to E2B API

## Production Best Practices

1. **Use Strong Passwords**: Change default `CHAINLIT_PASSWORD`
2. **Monitor Costs**: Set OpenAI spending limits
3. **Version Control**: Keep .env out of git
4. **Backup Code**: Regular git commits
5. **Update Dependencies**: `pip install --upgrade -r requirements.txt`

## Support

For issues:
- Check logs in Render dashboard
- Review error messages in the UI
- Open issue on GitHub: https://github.com/ayushm98/Devon/issues
