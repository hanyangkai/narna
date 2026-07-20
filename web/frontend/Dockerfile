FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_URL=
ARG VITE_PADDLE_CLIENT_TOKEN=
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_PADDLE_CLIENT_TOKEN=$VITE_PADDLE_CLIENT_TOKEN
COPY web/frontend/package.json web/frontend/package-lock.json* ./
RUN npm install
COPY web/frontend .
RUN npm run build

FROM nginx:alpine
COPY web/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
