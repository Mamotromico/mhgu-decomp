extern "C" {
void func_6056e4d8(void *);
void func_6058e6ac(void *);
void func_6058e684(void *p) {
    func_6056e4d8(p);
    *(unsigned *)((char *)p + 0x50) = 0;
    func_6058e6ac(p);
    *(unsigned *)((char *)p + 0x54) = 0;
}
}