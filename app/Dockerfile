FROM node:20-bullseye
WORKDIR /app
RUN npm i -g expo-cli

# Install deps before copying source for better caching
COPY package.json package-lock.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 19006
# Remove CI=1 so Metro watch mode works
# ENV CI=1   <-- delete or comment this out

CMD ["npx","expo","start","--web"]
