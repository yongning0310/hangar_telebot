
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # logger.error(f"An error occurred in {func.__name__}: {e}")
            update = args[0]
            update.message.reply_text("An error occurred. Please try again.")
    return wrapper