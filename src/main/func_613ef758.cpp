extern "C" void func_6130cc24(void *);

struct T {
    char pad[0x30];
    unsigned char b;
};

extern "C" void func_613ef758(T *p) {
    func_6130cc24(p);
    p->b = 0;
}