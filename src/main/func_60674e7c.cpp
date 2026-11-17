extern "C" void func_6065cb3c(void *, int);
extern "C" void func_6056dfac(void);

extern "C" void func_60674e7c(char *p) {
    func_6065cb3c(p, 0x1f);
    func_6056dfac();
    *(char *)(p + 0x3c) = 0;
}