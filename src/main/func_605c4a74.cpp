extern "C" void func_605c453c(void *);

extern "C" void func_605c4a74(char *p, unsigned v){
    *(unsigned *)(p + 0x4c) = v;
    func_605c453c(p);
}