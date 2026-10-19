extern "C" void* func_60614768(void* self, void* value) {
    void* p = *(void**)((char*)self + 0x54);
    if (p != 0) {
        *(void**)((char*)p + 0x7c) = value;
    }
    return p;
}