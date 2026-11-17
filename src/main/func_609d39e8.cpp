extern "C" int func_609f4e74(int, int);

extern "C" void func_609d39e8(char *p, int val) {
    func_609f4e74((int)(long)p, val);
    *(int *)(p + 0xd40) = val;
    *(int *)(p + 0xd48) = val;
}