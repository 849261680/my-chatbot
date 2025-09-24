# 智能聊天机器人
# 依赖: pip install google-genai python-dotenv

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import SYSTEM_INSTRUCTION, SYSTEM_PROMPTS, DEFAULT_PROMPT

# 加载环境变量
load_dotenv()


class ChatBot:
    def __init__(self):
        """初始化聊天机器人"""
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.model = "gemini-2.5-pro"  # 使用官方支持的模型名称
        self.conversation_history = []
        self.current_prompt = self._load_last_prompt()  # 加载上次使用的提示词
        self.chat_log_file = f"chat_{self.current_prompt}.md"  # 对话记录文件
        self._load_chat_history()  # 加载历史对话
        
        # 生成配置 - 符合官方最佳实践
        self.config = types.GenerateContentConfig(
            temperature=2,  
            thinking_config=types.ThinkingConfig(
                thinking_budget=2000,  # 控制推理token预算
                include_thoughts=True,  # 官方推荐：显示推理过程
            ),
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            system_instruction=SYSTEM_PROMPTS[self.current_prompt],
        )
    
    def add_message(self, role, text):
        """添加消息到对话历史"""
        self.conversation_history.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )
    
    def get_response(self, user_input):
        """获取AI回复"""
        # 添加用户输入到历史
        self.add_message("user", user_input)
        # 保存用户输入到日志
        self._save_to_log("user", user_input)
        
        try:
            # 生成回复 - 使用官方推荐的简洁方式
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=self.conversation_history,
                config=self.config,
            ):
                # 显示推理过程 - 使用官方推荐的简洁方式
                for part in chunk.candidates[0].content.parts:
                    if not part.text:
                        continue
                    elif part.thought:
                        print(f"\n🧠 [推理过程]: {part.text}", flush=True)
                
                # 简化的文本处理 - 符合官方示例
                if chunk.text:
                    response_text += chunk.text
                    print(chunk.text, end="", flush=True)
            
            # 添加AI回复到历史
            if response_text:
                self.add_message("model", response_text)
                # 保存AI回复到日志
                self._save_to_log("model", response_text)
            
            return response_text
            
        except Exception as e:
            # 更详细的错误处理
            if "API_KEY" in str(e):
                error_msg = "❌ API密钥错误，请检查GEMINI_API_KEY环境变量"
            elif "quota" in str(e).lower():
                error_msg = "❌ API配额已用完，请稍后再试"
            elif "rate" in str(e).lower():
                error_msg = "❌ 请求频率过高，请稍后再试"
            else:
                error_msg = f"❌ API请求失败: {str(e)}"
            
            print(error_msg)
            return error_msg
    
    def show_welcome(self):
        """显示欢迎信息"""
        print("🤖 智能聊天机器人已启动！")
        print("=" * 50)
        if os.path.exists(self.chat_log_file):
            history_count = len(self.conversation_history)
            print(f"📚 已加载 {history_count} 条历史对话记录")
        print(f"🎯 当前提示词: {self.current_prompt}")
        print("💡 输入 'quit', 'exit' 或 'bye' 退出")
        print("💡 输入 'clear' 清空对话历史")
        print("💡 输入 'prompt:提示词名' 切换提示词")
        print("💡 输入 'prompt:list' 查看所有提示词")
        print(f"💡 对话记录将自动保存到 {self.chat_log_file}")
        print("=" * 50)
    
    def _load_last_prompt(self):
        """加载上次使用的提示词"""
        try:
            if os.path.exists('.last_prompt'):
                with open('.last_prompt', 'r', encoding='utf-8') as f:
                    last_prompt = f.read().strip()
                    if last_prompt in SYSTEM_PROMPTS:
                        return last_prompt
        except Exception:
            pass
        return DEFAULT_PROMPT

    def _save_last_prompt(self):
        """保存当前使用的提示词"""
        try:
            with open('.last_prompt', 'w', encoding='utf-8') as f:
                f.write(self.current_prompt)
        except Exception as e:
            print(f"⚠️ 保存提示词状态失败: {e}")

    def _load_chat_history(self):
        """加载历史对话记录"""
        if os.path.exists(self.chat_log_file):
            try:
                with open(self.chat_log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单解析MD格式，提取对话内容重建历史
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('**😊 你:**'):
                            text = line.replace('**😊 你:**', '').strip()
                            if text:
                                self.add_message("user", text)
                        elif line.startswith('**🤖 AI:**'):
                            text = line.replace('**🤖 AI:**', '').strip()
                            if text:
                                self.add_message("model", text)
            except Exception as e:
                print(f"⚠️ 加载历史对话失败: {e}")

    def _save_to_log(self, role, message):
        """保存对话到MD文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 确定角色显示
        role_display = "😊 你" if role == "user" else "🤖 AI"
        
        # 格式化消息
        log_entry = f"\n**{role_display}:** {message}\n*时间: {timestamp}*\n"
        
        try:
            with open(self.chat_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️ 保存对话记录失败: {e}")

    def switch_prompt(self, prompt_name):
        """切换系统提示词"""
        if prompt_name in SYSTEM_PROMPTS:
            self.current_prompt = prompt_name
            self.chat_log_file = f"chat_{prompt_name}.md"
            # 保存当前使用的提示词
            self._save_last_prompt()
            # 重建配置
            self.config = types.GenerateContentConfig(
                temperature=2,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=2000,
                    include_thoughts=True,
                ),
                media_resolution="MEDIA_RESOLUTION_MEDIUM",
                system_instruction=SYSTEM_PROMPTS[prompt_name],
            )
            # 清空并重新加载历史
            self.conversation_history = []
            self._load_chat_history()
            print(f"\n✅ 已切换到 '{prompt_name}' 提示词")
            print(f"📁 对话记录文件: {self.chat_log_file}")
            history_count = len(self.conversation_history)
            if history_count > 0:
                print(f"📚 已加载 {history_count} 条历史记录\n")
            else:
                print("📚 暂无历史记录\n")
        else:
            print(f"❌ 提示词 '{prompt_name}' 不存在")
            self.list_prompts()

    def list_prompts(self):
        """显示所有可用的提示词"""
        print("\n📋 可用的系统提示词：")
        for key, value in SYSTEM_PROMPTS.items():
            status = " (当前)" if key == self.current_prompt else ""
            preview = value[:30].replace('\n', ' ') + "..."
            print(f"   {key}{status} - {preview}")
        print()

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("\n✨ 对话历史已清空\n")
    
    def run(self):
        """运行聊天机器人"""
        self.show_welcome()
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n😊 你: ").strip()
                
                # 检查退出命令
                if user_input.lower() in ['quit', 'exit', 'bye', '退出', '再见']:
                    self._save_last_prompt()  # 保存当前提示词状态
                    print("\n👋 再见！感谢使用聊天机器人！")
                    break
                
                # 检查清空历史命令
                if user_input.lower() in ['clear', '清空']:
                    self.clear_history()
                    continue
                
                # 检查提示词切换命令
                if user_input.lower().startswith('prompt:'):
                    prompt_name = user_input[7:].strip()  # 去掉 'prompt:' 前缀
                    if prompt_name == 'list':
                        self.list_prompts()
                    elif prompt_name:
                        self.switch_prompt(prompt_name)
                    else:
                        print("❌ 请提供提示词名称，格式：prompt:提示词名")
                        self.list_prompts()
                    continue
                
                # 检查空输入
                if not user_input:
                    print("请输入一些内容...")
                    continue
                
                # 获取并显示AI回复
                print("\n🤖 AI: ", end="", flush=True)
                self.get_response(user_input)
                print()  # 换行
                
            except KeyboardInterrupt:
                self._save_last_prompt()  # 保存当前提示词状态
                print("\n\n👋 检测到 Ctrl+C，正在退出...")
                break
            except EOFError:
                self._save_last_prompt()  # 保存当前提示词状态
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {str(e)}")


def main():
    """主函数"""
    # 检查API密钥
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ 错误: 未找到 GEMINI_API_KEY")
        print("请在 .env 文件中设置你的 Google AI Studio API 密钥")
        print("格式: GEMINI_API_KEY=你的密钥")
        sys.exit(1)
    
    # 启动聊天机器人
    chatbot = ChatBot()
    chatbot.run()


if __name__ == "__main__":
    main()
