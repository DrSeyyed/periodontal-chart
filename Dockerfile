FROM node:24-alpine

WORKDIR /app
COPY . .

RUN npm install
RUN npm run build
EXPOSE 5171
ENV PORT=5171
ENV BODY_SIZE_LIMIT=50M
CMD ["sh","-lc","node build --host 0.0.0.0 --port ${PORT:-5171}"]