

def allow_without_subscription(func):
    func.allow_without_subscription = True
    return func
