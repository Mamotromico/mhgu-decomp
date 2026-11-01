extern "C" void* func_602828cc(void* p, void* arg) {
    void* obj = *(void**)((char*)p + 0x2640);
    if (!obj)
        return 0;
    void* vtbl = *(void**)obj;
    void* (*fn)(void*, void*) = *(void* (**)(void*, void*))((char*)vtbl + 0x44);
    return fn(obj, arg);
}