extern "C" {

struct S {
    char pad[0x60];
};

void func_6080488c(char *base, char *src);
char *func_609fa3d8(void *p);

void func_609fb254(struct S *s)
{
    char *r1 = func_609fa3d8(s);
    func_6080488c((char *)s + 0x60, r1);
}

}