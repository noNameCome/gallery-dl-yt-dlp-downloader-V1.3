import sys
import traceback
import logging
from gui.app import run_app

if __name__ == '__main__':
    try:
        # 모든 로거의 레벨을 INFO로 설정
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.setLevel(logging.INFO)
        
        # 루트 로거 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        logging.info("프로그램 시작")
        run_app()
    except Exception as e:
        error_msg = f"오류 발생: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        
        # 오류 발생 시 메시지 박스로 표시
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("오류", f"프로그램 실행 중 오류가 발생했습니다.\n\n{str(e)}")
        sys.exit(1)
  