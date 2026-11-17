namespace nn { namespace os { struct MutexType; void LockMutex(MutexType*); } }

extern "C" void func_6130c6f8(nn::os::MutexType* m) {
    nn::os::LockMutex(m);
}