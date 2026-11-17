extern "C" void func_605c4a74(void *, int);

extern "C" void func_6054b79c(void *p) {
    void *q = *(void **)((char *)p + 0x4c);
    if (q == 0)
        return;
    func_605c4a74(q, 0);
}