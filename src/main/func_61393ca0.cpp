extern "C" void func_61393ca0(void* arg) {
    char* base = (char*)arg;
    char* end = base + 0x8;
    char* p = *(char**)(base + 0xc);
    while (p != end) {
        *(void**)(p + 0x8) = 0;
        p = *(char**)(p + 0x4);
    }
}