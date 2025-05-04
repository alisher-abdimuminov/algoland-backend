#define _GNU_SOURCE
#define _POSIX_C_SOURCE 199309L
#include <time.h>
#include <stdio.h>
#include <fcntl.h>
#include <errno.h>
#include <sched.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <limits.h>
#include <seccomp.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <sys/prctl.h>
#include <sys/types.h>
#include <linux/prctl.h>
#include <sys/syscall.h>
#include <linux/sched.h>
#include <sys/resource.h>


void setup_seccomp() {
    scmp_filter_ctx ctx;
    ctx = seccomp_init(SCMP_ACT_ALLOW);

    // fork larni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(fork), 0); // forkni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(vfork), 0); // vforkni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(clone), 0); // cloneni bloklash

    // Boshqa jarayonlarni o‘ldirish yoki boshqarishni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(kill), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(tgkill), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(tkill), 0);

    // Rootga o‘tish yoki foydalanuvchi identifikatorini o‘zgartirish
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(setuid), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(setgid), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(setreuid), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(setregid), 0);

    // Fayl tizimiga xavfli murojaatlar
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(mount), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(umount2), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(kexec_load), 0);     // boshqa yadro yuklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(ptrace), 0);         // boshqa jarayonlarni kuzatish
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(mknod), 0);          // yangi blok device yaratish
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(chmod), 0);          // fayl huquqlari o‘zgarishi
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(fchmod), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(chown), 0);          // fayl egasini o‘zgartirish
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(fchown), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(lchown), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(syslog), 0);

    // Device ochish yoki terminal interfeysiga ulanmaslik
    // seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(ioctl), 0);

    // Network yaratish yoki ulanadigan harakatlar
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(socket), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(connect), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(bind), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(accept), 0);
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(listen), 0);

    // Rebootni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_KILL, SCMP_SYS(reboot), 0);

    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(unlink), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(unlinkat), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(rmdir), 0);

    
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(openat), 1, SCMP_CMP(2, SCMP_CMP_MASKED_EQ, O_CREAT, O_CREAT));

    // ls ni bloklash (go uchun)
    // seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(getdents64), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(getdents), 0);

    // pwd ni bloklash
    seccomp_rule_add(ctx, SCMP_ACT_ERRNO(EPERM), SCMP_SYS(readlink), 0);

    seccomp_load(ctx);
}


void set_limits(int memory_limit, int time_limit, int process_limit) {
    struct rlimit limit;

    // Memory limit
    limit.rlim_cur = limit.rlim_max = memory_limit * 1024 * 1024;
    setrlimit(RLIMIT_AS, &limit);

    // Time limit
    limit.rlim_cur = limit.rlim_max = time_limit;
    setrlimit(RLIMIT_CPU, &limit);

    // Process limit
    limit.rlim_cur = limit.rlim_max = process_limit;
    setrlimit(RLIMIT_NPROC, &limit);

    limit.rlim_cur = limit.rlim_max = 1024 * 1024;
    setrlimit(RLIMIT_FSIZE, &limit);

    limit.rlim_cur = limit.rlim_max = 64;
    setrlimit(RLIMIT_NOFILE, &limit);

    limit.rlim_cur = limit.rlim_max = 8 * 1024 * 1024;
    setrlimit(RLIMIT_STACK, &limit);
}


void write_meta(const char *meta_file, int exit_code, int signal_code, double exec_time, long max_rss) {
    FILE *meta = fopen(meta_file, "w");
    if (meta) {
        fprintf(meta, "{ \"exit_code\": %d, \"signal\": %d, \"time\": %.3f, \"memory\": %ld }", exit_code, signal_code, exec_time * 1000, max_rss);
        fclose(meta);
    }
}


int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Foydalanish: %s <buyruq>\n", argv[0]);
        return 1;
    }

    pid_t pid = fork();
    if (pid == -1) {
        perror("fork xatosi");
        return 1;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    if (pid == 0) {
        int out_fd = open("output.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (out_fd == -1) {
            perror("output.txt ochilmadi");
            exit(1);
        }
        dup2(out_fd, STDOUT_FILENO);
        close(out_fd);

        int err_fd = open("error.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (err_fd == -1) {
            perror("error.txt ochilmadi");
            exit(1);
        }
        dup2(err_fd, STDERR_FILENO);
        close(err_fd);

        setup_seccomp();
        set_limits(128, 2, 32);
        execvp(argv[1], &argv[1]);

        perror("execvp error");
        exit(1);
    } else {
        int status;
        waitpid(pid, &status, 0);
        clock_gettime(CLOCK_MONOTONIC, &end);

        double exec_time = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
        int exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
        int signal_code = WIFSIGNALED(status) ? WTERMSIG(status) : 0;

        struct rusage usage;
        getrusage(RUSAGE_CHILDREN, &usage);
        long max_rss = usage.ru_maxrss;

        write_meta("meta.json", exit_code, signal_code, exec_time, max_rss);
    }

    return 0;
}
