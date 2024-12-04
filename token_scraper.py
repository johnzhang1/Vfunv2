from playwright.sync_api import sync_playwright
import time
import json
import logging
import re

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_latest_tokens():
    with sync_playwright() as p:
        # 使用无头模式，并模拟真实浏览器
        browser = p.chromium.launch(
            headless=False,  # 改为非无头模式，方便调试
            slow_mo=500,     # 添加延迟，方便观察
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # 导航到网站并等待网络空闲
            logger.info("Navigating to website...")
            page.goto("https://fun.virtuals.io/", wait_until="networkidle", timeout=60000)
            
            # 等待并尝试获取数据
            page.wait_for_load_state('networkidle', timeout=60000)
            
            # 使用更复杂的页面评估和数据提取
            tokens = page.evaluate('''
                () => {
                    const extractTokens = () => {
                        const tokenElements = document.querySelectorAll('div.card-container');
                        console.log(`Found ${tokenElements.length} token elements`);
                        
                        if (tokenElements.length > 0) {
                            const tokens = [];
                            for (let i = 0; i < Math.min(20, tokenElements.length); i++) {
                                const element = tokenElements[i];
                                
                                // 提取市场资本的函数
                                const extractMarketCap = () => {
                                    const marketCapElement = element.querySelector('p[class*="text-[#00FFA3]"]');
                                    if (marketCapElement) {
                                        const text = marketCapElement.textContent.trim();
                                        const match = text.match(/Market Cap\\s*:\\s*([\\d.]+[kKmMbB]?)/);
                                        return match ? match[1] : '';
                                    }
                                    return '';
                                };
                                
                                // 提取文本的通用函数
                                const extractText = (selector) => {
                                    const el = element.querySelector(selector);
                                    return el ? el.textContent.trim() : '';
                                };

                                // 提取链接的函数
                                const extractLink = () => {
                                    const linkElement = element.querySelector('a[href^="/profile/"]');
                                    if (linkElement) {
                                        return {
                                            href: linkElement.getAttribute('href'),
                                            address: linkElement.href.split('/profile/')[1]
                                        };
                                    }
                                    return null;
                                };

                                // 提取agent链接
                                const extractAgentLink = () => {
                                    const containerElement = element.closest('a[href^="/agents/"]');
                                    if (containerElement) {
                                        return {
                                            href: containerElement.getAttribute('href'),
                                            address: containerElement.href.split('/agents/')[1]
                                        };
                                    }
                                    return null;
                                };
                                
                                const token = {
                                    name: extractText('div.text-white p:first-child'),
                                    symbol: extractText('p[class*="text-white/50"]'),
                                    marketCap: extractMarketCap(),
                                    description: extractText('p[class*="text-[#A0CFCB]"]') || extractText('p.text-base'),
                                    createdTime: extractText('p[class*="text-[#FCE94B]"]:last-child'),
                                    profileLink: extractLink(),
                                    agentLink: extractAgentLink()
                                };
                                
                                console.log('Extracted token:', token);
                                
                                if (token.name || token.symbol) {
                                    tokens.push(token);
                                }
                            }
                            return tokens;
                        }
                        return [];
                    };
                    
                    return extractTokens();
                }
            ''')
            
            return tokens
            
        except Exception as e:
            logger.error(f"Detailed Error: {e}", exc_info=True)
            return None
        
        finally:
            browser.close()

def main():
    tokens = get_latest_tokens()
    if tokens:
        print("\nLatest 20 tokens from fun.virtuals.io:")
        print("-" * 50)
        for i, token in enumerate(tokens, 1):
            print(f"{i}. Name: {token['name']}")
            print(f"   Symbol: {token['symbol']}")
            print(f"   Market Cap: {token['marketCap']}")
            print(f"   Created: {token['createdTime']}")
            if token['profileLink']:
                print(f"   Profile: https://fun.virtuals.io{token['profileLink']['href']}")
                print(f"   Profile Address: {token['profileLink']['address']}")
            if token['agentLink']:
                print(f"   Agent: https://fun.virtuals.io{token['agentLink']['href']}")
                print(f"   Agent Address: {token['agentLink']['address']}")
            print(f"   Description: {token['description'][:100]}...")
            print("-" * 50)
        
        # 将代币信息保存到 JSON 文件
        with open('latest_tokens.json', 'w', encoding='utf-8') as json_file:
            json.dump(tokens, json_file, indent=4, ensure_ascii=False)
            print("\nToken data saved to latest_tokens.json")
    else:
        print("Failed to retrieve tokens.")

if __name__ == "__main__":
    main()