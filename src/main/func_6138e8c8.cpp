extern "C" void func_6138e8c8(char *self) {
    unsigned char index = *(unsigned char *)(self + 0xc0);
    void *object = *(void **)(self + (index << 2) + 0xc4);
    void (*method)(void *) = *(void (**)(void *))((char *)*(void **)object + 0x1c);
    method(object);
}